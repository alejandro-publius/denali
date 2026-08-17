"""MCP server — the study's findings, and the tool that produced them.

Five tools, in two halves.

LOOKUPS INTO OUR RESULT. `reversibility` and `provenance` answer what WE found:
measured reversibility for a program if we scored it, a prediction with
uncertainty if we did not, plus the generated next-experiment proposal and the
controls behind the whole thing. Read results/frozen/ only, never recompute.

THE TOOL ITSELF, ON THE CALLER'S OWN DATA. `audit`, `rerank` and `baseline` are
the packaged check from packages/denali-audit, exposed verbatim. An agent hands
them its own gene-set table -- as arrays, or as a path to whatever its enrichment
tool already wrote -- and gets back how much of its ranking is set size, which of
its top entries do not survive the correction, and what a size-only predictor
scores on its own evaluation. Nothing about denali is involved in the answer.
Without these the server was a database of our findings; with them it is the
instrument, reachable by any agent that speaks MCP.

The two halves are deliberately asymmetric, and that asymmetry is the design.
This server will APPLY a correction to your ranking and it will not NOMINATE
anything from ours: ask it which program to chase and it refuses, citing the
0.4375 balanced accuracy its own predictor scored on held-out data. A tool that
told you what to chase on the strength of a predictor that failed would be
committing the error this project exists to measure.

    .venv/bin/python -m src.mcp_server
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from src.answers import HELDOUT_WARNING, SCOPE, VALIDATION, refuse, unscored
from src.next_experiment import propose

# src/__init__.py puts the vendored packages/denali-audit on the path, so the
# server serves the SAME function the study runs and the CLI ships -- not a
# server-side reimplementation of it.
from denali_audit.adapters import describe_failure, detect
from denali_audit.core import audit as _audit
from denali_audit.core import baseline as _baseline
from denali_audit.core import rerank as _rerank

# Anchored to this file, NOT to the caller's cwd. An MCP client launches the
# server from wherever it happens to be, so a relative path here meant a
# stranger wiring this into their agent got FileNotFoundError on
# results/frozen/heldout_evaluation.json. Found by starting the server from
# /tmp the way a client actually would.
FROZEN = Path(__file__).resolve().parents[1] / "results" / "frozen"
# `mcp` is an optional dependency. The server ships as a tool for agents; the study
# reproduces without it. Importing FastMCP at module scope meant a clone that had not
# installed one extra package could not even IMPORT this file -- which aborted the whole
# invariant suite, because the suite imports this module to check the refusal paths.
# Every check above that import already passed and none of them were reported.
try:
    from mcp.server.fastmcp import FastMCP
    mcp = FastMCP("denali")
except ModuleNotFoundError:                                  # pragma: no cover
    class _Unserved:
        """Keeps the tool functions importable and callable without `mcp` present."""
        @staticmethod
        def tool(*_a, **_k):
            return lambda fn: fn

        @staticmethod
        def run():
            raise SystemExit("pip install mcp to serve this; the study reproduces "
                             "without it and every tool function is importable now.")
    mcp = _Unserved()

_S = pd.read_csv(FROZEN / "program_summary.csv")
_P = json.loads((FROZEN / "predictor.json").read_text())
_H = pd.read_csv(FROZEN / "heldout.csv")


@mcp.tool()
def reversibility(program: str) -> dict:
    """Reversibility of a gene program in the K562 genome-scale CRISPRi screen.

    Returns a measured result if the program is in the frozen 50-program matrix,
    otherwise a prediction with uncertainty. Always returns the generated
    next-experiment proposal and the scope limit.

    Args:
        program: MSigDB program name, e.g. HALLMARK_CHOLESTEROL_HOMEOSTASIS
    """
    blocked = refuse(program)
    if blocked is not None:
        return blocked

    # Case-insensitive, matching the refusals. A companion fix made `refuse()`
    # case-insensitive and left the LOOKUP exact, which is the worse half of the
    # asymmetry: a lowercase program name returned UNSCORED, i.e. a confident
    # wrong answer ("not in the frozen matrix") rather than a refusal. Agents
    # normalise case; MSigDB names are conventionally upper.
    _q = (program or "").strip()
    row = _S[_S.program.str.upper() == _q.upper()]
    if not row.empty:
        r = row.iloc[0]
        program = r.program          # answer under the canonical name
        return {
            "program": program, "status": "MEASURED",
            "rank_of_50": int(r.rank_by_R_p),
            "knockdowns_that_moved_it": int(r.n_hits_q05),
            "call": r.reversibility_call, "call_plain": r.call_plain,
            "passes_measurability_gate": bool(r.passes_measurability_gate),
            "measurability_limited": bool(r.measurability_limited),
            "predicted_from_measurability_alone": float(r.R_p_predicted_from_measurability),
            "residual_that_could_be_biology": float(r.R_p_residual_after_measurability),
            "is_held_out_program": bool(r.is_held_out_program),
            "next_experiment": propose(program, _S),
            "scope_limit": SCOPE,
        }

    h = _H[_H.program == program]
    if not h.empty:
        r = h.iloc[0]
        return {
            "program": program, "status": "HELD_OUT_AND_SCORED",
            "predicted_R_p": float(r.R_p_predicted),
            "observed_R_p": float(r.R_p_observed),
            "knockdowns_that_moved_it": int(r.n_hits_q05),
            "warning": HELDOUT_WARNING,
            "scope_limit": SCOPE,
        }

    return unscored(program, _P["residual_sd"])


@mcp.tool()
def provenance() -> dict:
    """Provenance, controls and the honest limits of this dataset."""
    return json.loads((FROZEN / "provenance.json").read_text())


# --------------------------------------------------------------------------
# The product, on the caller's own data. Neither tool below reads results/frozen/
# or knows anything about denali's screen.

def _load(table_path: str):
    """Read the caller's table and work out which columns are which.

    Returns (Mapping, error_dict). Errors come back as a value rather than an
    exception because an MCP client renders a returned dict and swallows a
    traceback into a wall of red -- and the most useful thing this can say to an
    agent holding an unrecognised table is which columns it DID find.
    """
    p = Path(table_path).expanduser()
    if not p.exists():
        return None, {"status": "ERROR", "reason": f"no such file: {table_path}"}
    sep = "\t" if p.suffix.lower() in (".tsv", ".tab", ".txt") else None
    try:
        df = pd.read_csv(p, sep=sep, engine="python")
    except Exception as e:                                   # pragma: no cover
        return None, {"status": "ERROR", "reason": f"could not read {p.name}: {e}"}
    m = detect(df)
    if m is None:
        return None, {"status": "UNRECOGNISED_FORMAT",
                      "reason": describe_failure(df),
                      "columns_found": [str(c) for c in df.columns]}
    return (df, m), None


def _rows(sets: list[dict]) -> tuple[tuple, None] | tuple[None, dict]:
    """Row dicts -> (sizes, hits, names). An agent holds rows, not three
    parallel arrays whose alignment nothing checks; over JSON-RPC a caller can
    silently drop one element of one array and get a confidently wrong answer.
    So rows are the primary shape and a row missing either field is refused
    rather than guessed at."""
    if not isinstance(sets, list) or not sets:
        return None, {"status": "REFUSED", "reason": "sets must be a non-empty list "
                                                     "of rows.", "scope_limit": SCOPE}
    sizes, hits, names = [], [], []
    for i, row in enumerate(sets):
        if not isinstance(row, dict):
            return None, {"status": "REFUSED",
                          "reason": f"row {i} is not an object with size and hits.",
                          "scope_limit": SCOPE}
        size = row.get("size", row.get("n_present", row.get("term_size")))
        hit = row.get("hits", row.get("n_hits", row.get("intersection_size")))
        if size is None or hit is None:
            return None, {
                "status": "REFUSED",
                "reason": f"row {i} is missing size or hits. Every row needs how "
                          f"many members the set had and how many came back "
                          f"significant; this tool will not infer either.",
                "row": row, "scope_limit": SCOPE}
        sizes.append(float(size))
        hits.append(float(hit))
        names.append(str(row.get("name", row.get("term_name", f"set_{i}"))))
    return (sizes, hits, names), None


@mcp.tool()
def audit(sizes: list[float] | None = None,
          hits: list[float] | None = None,
          corr: list[float] | None = None,
          table_path: str | None = None,
          sets: list[dict] | None = None) -> dict:
    """How much of YOUR gene-set ranking is set size rather than biology?

    This is the check itself, run on your data. It has nothing to do with
    denali's screen: give it one row per gene set and it reports what share of
    the variance in your hit counts is predicted by how big the sets are, with a
    verdict of CONFOUNDED, PARTIALLY CONFOUNDED, NOT SIZE-DOMINATED, or
    UNDETERMINED when every set is the same size and the question cannot be
    asked. Where a reference distribution applies it also says where your screen
    sits against 1,272 published ones.

    It returns a property of your RANKING. It does not score, order or nominate
    any set in it.

    Args:
        sizes: members measured per set, one number per set (min 8 sets)
        hits: significant results per set, same order as sizes
        corr: optional mean inter-gene correlation per set; upgrades the
            estimate from size-only to the full variance-inflation factor
        table_path: instead of arrays, a path to the table your enrichment tool
            already wrote. g:Profiler, DAVID, clusterProfiler, Enrichr, fgsea,
            GSEA desktop, MAGeCK, drugZ and BAGEL are recognised without flags.
        sets: instead of arrays, one row per set: {"name", "size", "hits"}.
            Preferred when you are holding the table in memory -- the row keeps
            each set's size and hits together, so nothing depends on two lists
            staying the same length and the same order.
    """
    if sets is not None:
        parsed, err = _rows(sets)
        if err:
            return err
        s, h, _ = parsed
        try:
            return _audit(s, h, corr)
        except ValueError as e:
            return {"status": "REFUSED", "reason": str(e), "scope_limit": SCOPE}
    if table_path:
        loaded, err = _load(table_path)
        if err:
            return err
        df, m = loaded
        res = _audit(m.size, m.hits, m.corr)
        res["input_format"] = m.fmt
        if m.approximate:
            res["input_warning"] = m.note
        return res
    if sizes is None or hits is None:
        return {"status": "ERROR",
                "reason": "give either sizes and hits, or table_path."}
    try:
        return _audit(sizes, hits, corr)
    except ValueError as e:
        return {"status": "ERROR", "reason": str(e)}


@mcp.tool()
def rerank(sizes: list[float] | None = None,
           hits: list[float] | None = None,
           names: list[str] | None = None,
           top: int = 10,
           table_path: str | None = None,
           sets: list[dict] | None = None) -> dict:
    """Apply the size correction to YOUR ranking and report what does not survive.

    Regresses log10(1+hits) on set size and re-ranks by the residual, so a set is
    scored on how far it beats what its size alone predicts. Returns which of
    your top entries LEFT the top once that is done, and how far each fell.

    This is the inverse of a candidate list and it is the only direction this
    tool moves in: it names the entries your current ranking is least able to
    justify, never the ones to chase. If every set is the same size it says so
    and reports nothing, because a correction that cannot move anything is not a
    test your ranking passed.

    Args:
        sizes: members measured per set, one number per set (min 8 sets)
        hits: significant results per set, same order as sizes
        names: optional labels for your sets, echoed back on the rows that moved
        top: how many of your top entries to check (default 10)
        table_path: instead of arrays, a path to the table your enrichment tool
            already wrote; the same formats `audit` recognises.
        sets: instead of arrays, one row per set: {"name", "size", "hits"}.
            Preferred when you are holding the table in memory.
    """
    if sets is not None:
        parsed, err = _rows(sets)
        if err:
            return err
        s, h, nm = parsed
        try:
            res = _rerank(s, h, nm, top=top)
        except ValueError as e:
            return {"status": "REFUSED", "reason": str(e), "scope_limit": SCOPE}
        # The correction is only meaningful next to the verdict on the same
        # table: "three of your top ten left" reads very differently when the
        # ranking was NOT SIZE-DOMINATED to begin with.
        try:
            a = _audit(s, h)
            res["your_ranking"] = {"verdict": a.get("verdict"),
                                   "r2_size_alone": a.get("r2_size_alone"),
                                   "reading": a.get("reading")}
        except ValueError:
            pass
        res["predictor_validation"] = VALIDATION
        res["scope_limit"] = SCOPE
        return res
    if table_path:
        loaded, err = _load(table_path)
        if err:
            return err
        df, m = loaded
        nm = df[m.set_col] if m.set_col in df.columns else None
        res = _rerank(m.size, m.hits, nm, top=top)
        res["input_format"] = m.fmt
        return res
    if sizes is None or hits is None:
        return {"status": "ERROR",
                "reason": "give either sizes and hits, or table_path."}
    try:
        return _rerank(sizes, hits, names, top=top)
    except ValueError as e:
        return {"status": "ERROR", "reason": str(e)}


@mcp.tool()
def baseline(sizes: list[float] | None = None,
             hits: list[float] | None = None,
             predicted: list[float] | None = None,
             metric: str | None = None,
             k: int = 10,
             table_path: str | None = None,
             predicted_column: str | None = None,
             sets: list[dict] | None = None) -> dict:
    """How much of YOUR model's score is recoverable from set size, with no model?

    Give it your predictions and the truth you score them against, and it
    returns the score a predictor that sees ONLY how big each set is achieves
    on your own evaluation, next to yours, plus the difference. The size-only
    baseline is leave-one-out, so it never saw the row it predicts.

    Every team reporting "our model beats baseline" computes its own baseline,
    differently, and nobody can check it. This makes that number a callable
    artifact rather than an assertion.

    It is a MEASUREMENT and not a verdict. It does not say any model is bad, it
    does not rank models, and a model can be worth having without beating this.

    Args:
        sizes: members measured per set, one number per set (min 8 sets)
        hits: the truth your model is scored against, same order as sizes
        predicted: your model's score per set, same order as sizes
        metric: how YOU evaluate. One of spearman, pearson, r2, mae, rmse,
            top_k_overlap. Never guessed -- a baseline scored with a different
            metric than yours is not a comparison. Pass "none" to get the
            baseline's per-set predictions back and score them yourself.
        k: k for top_k_overlap (default 10)
        table_path: instead of arrays, a path to the table your enrichment tool
            wrote; the same formats `audit` recognises. Needs predicted_column.
        predicted_column: with table_path, the column holding your predictions.
        sets: instead of arrays, one row per set:
            {"name", "size", "hits", "predicted"}.
    """
    if sets is not None:
        parsed, err = _rows(sets)
        if err:
            return err
        s, h, _ = parsed
        preds = [r.get("predicted", r.get("prediction", r.get("score")))
                 for r in sets]
        if any(v is None for v in preds):
            return {"status": "REFUSED",
                    "reason": "every row needs a 'predicted' value -- your "
                              "model's score for that set. This tool will not "
                              "infer it.",
                    "scope_limit": SCOPE}
        try:
            return _baseline(s, h, [float(v) for v in preds], metric=metric, k=k)
        except ValueError as e:
            return {"status": "REFUSED", "reason": str(e), "scope_limit": SCOPE}
    if table_path:
        if not predicted_column:
            return {"status": "REFUSED",
                    "reason": "name the column holding your predictions with "
                              "predicted_column. Guessing which column is a "
                              "model score would make every number below a "
                              "different quantity from the one you report.",
                    "scope_limit": SCOPE}
        loaded, err = _load(table_path)
        if err:
            return err
        df, m = loaded
        if predicted_column not in df.columns:
            return {"status": "ERROR",
                    "reason": f"no column {predicted_column!r} in that table.",
                    "columns_found": [str(c) for c in df.columns]}
        try:
            res = _baseline(m.size, m.hits, df[predicted_column],
                            metric=metric, k=k)
        except ValueError as e:
            return {"status": "REFUSED", "reason": str(e), "scope_limit": SCOPE}
        res["input_format"] = m.fmt
        res["predicted_column"] = predicted_column
        if m.approximate:
            res["input_warning"] = m.note
        return res
    if sizes is None or hits is None or predicted is None:
        return {"status": "ERROR",
                "reason": "give sizes, hits and predicted, or table_path with "
                          "predicted_column, or sets."}
    try:
        return _baseline(sizes, hits, predicted, metric=metric, k=k)
    except ValueError as e:
        return {"status": "REFUSED", "reason": str(e), "scope_limit": SCOPE}


@mcp.tool()
def floor(screen_id: int) -> dict:
    """The published no-biology floor for one screen in the denali atlas.

    Given a BioGRID ORCS screen id, returns the share of that screen's gene-set
    hit ranking that is predicted by set size alone -- the value a method has to
    beat before any of its ranking is attributable to biology -- together with
    the atlas version, the content hash to cite, and the exact method.

    The number is looked up, not recomputed, so every caller gets the identical
    value and a citation that means one thing. A screen outside the atlas
    returns NOT_IN_ATLAS with the inclusion rule stated, rather than a guess.

    This is a property of a RANKING, not a quality score for a screen and not a
    criticism of the study that produced it. It names no gene and no gene set.

    Args:
        screen_id: BioGRID ORCS screen id, e.g. 100
    """
    from denali_audit.atlas import floor as _floor
    return _floor(screen_id)


if __name__ == "__main__":
    mcp.run()
