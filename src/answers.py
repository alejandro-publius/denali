"""The caveats the callable surface attaches to every answer.

Split out of `src/mcp_server.py` for one reason: the page claims the server
reports its own failure verbatim, and the only way to make that claim checkable
is for both to read the same string object. A copy-paste would drift silently
and the claim would quietly become false.

Every number here is read from `results/frozen/` at import. Nothing is typed in.
stdlib + pandas only, so the page can import this without the MCP dependency.
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

# Anchored to this file, NOT to the caller's cwd. An MCP client launches the
# server from wherever it happens to be, so a relative path here meant a
# stranger wiring this into their agent got FileNotFoundError on
# results/frozen/heldout_evaluation.json. Found by starting the server from
# /tmp the way a client actually would.
FROZEN = Path(__file__).resolve().parents[1] / "results" / "frozen"

_EVAL = json.loads((FROZEN / "heldout_evaluation.json").read_text())
_PROV = json.loads((FROZEN / "provenance.json").read_text())
_CTRL = pd.read_csv(FROZEN / "controls.csv")

CONCORDANCE = float(_CTRL.loc[_CTRL.control == "guide_pair_concordance", "value"].iloc[0])
R2_LO = _PROV["deciding_statistic"]["adjusted_r2_x_independent_only"]
R2_HI = _PROV["deciding_statistic"]["adjusted_r2_all_six"]
BAL = _EVAL["axis2_balanced_accuracy"]
TP = _EVAL["axis2_confusion"]["tp"]
N_GATE = _EVAL["n_passing_gate"]
N_HELD = _EVAL["n_heldout"]

SCOPE = (f"Pathway-level only. Guide-pair concordance is {CONCORDANCE:+.3f}, so "
         f"gene-level calls are not reproducible and no novel gene is named. "
         f"Between {R2_LO:.0%} and {R2_HI:.0%} of variance in apparent "
         f"reversibility is explained by how the programs were defined -- chiefly "
         f"their size -- not by their biology. A post-freeze check split the "
         f"features: measurement quality alone reaches only adj R2 0.152, set "
         f"construction alone 0.697.")

VALIDATION = (f"FAILED on held-out data: balanced accuracy {BAL:.4f}, worse than "
              f"chance, {TP} true positives. The predictor is reported, not "
              f"endorsed.")

HELDOUT_WARNING = (f"Held-out evaluation was UNDERPOWERED AND INCONCLUSIVE "
                   f"({N_GATE}/{N_HELD} passed the gate). Binary recovery was worse "
                   f"than chance. Treat predictions as unvalidated.")

UNSCORED_NOTE = ("Not in the frozen matrix. Supply measurability features to get a "
                 "prediction, or score it on the existing pipeline.")


def unscored(program: str, residual_sd: float) -> dict:
    """The answer for a program we never scored.

    Lives here rather than inside the server so the page can render the real
    response instead of a transcription of it. The interesting property of this
    branch is that the tool volunteers its own failure before it is asked.
    """
    return {
        "program": program,
        "status": "UNSCORED",
        "note": UNSCORED_NOTE,
        "prediction_uncertainty_sd": residual_sd,
        "predictor_validation": VALIDATION,
        "scope_limit": SCOPE,
    }


# --------------------------------------------------------------------------
# Query-time refusal.
#
# The build-time scope guard stops US publishing a gene-level claim. It does
# nothing when an AGENT calls the server, and the agent is the caller we cannot
# see. Prior art: CRISPR-GPT (Nat Biomed Eng 2025) hard-codes non-bypassable
# refusals and a single "I don't know" path rather than trusting the model to be
# careful. Same instinct, different risk surface.
#
# Our risk is not that someone asks for a pathogen sequence -- we have none. It
# is that a caller asks this server to nominate a gene, and the residual column
# is sitting right there looking like a candidate score. That is the misuse this
# project exists to prevent, so it is refused rather than served with a caveat.

_GENE_LIKE = __import__("re").compile(r"^[A-Z][A-Z0-9]{1,7}(-[A-Z0-9]+)?$")

REFUSAL = (
    "Refused: this server answers at the level of gene PROGRAMS, never genes. "
    f"Guide-pair concordance in this dataset is {CONCORDANCE:+.3f} -- two "
    "independent reagents against the same gene give uncorrelated scores, so no "
    "single-gene answer from this data is reproducible, including a flattering "
    "one. Ask about a program, e.g. HALLMARK_CHOLESTEROL_HOMEOSTASIS.")

NO_NOMINATION = (
    "Refused: this server does not rank or nominate. The residual column exists "
    "and is returned per program, but a ranked 'top candidates' list is the exact "
    "inference the pre-registration refuses to make -- and the predictor behind "
    f"it failed its own held-out evaluation at balanced accuracy {BAL}. Sort the "
    "frozen table yourself if you want an ordering; this tool will not hand you "
    "one that looks endorsed.")


def refuse(program: str) -> dict | None:
    """Return a refusal if this query is asking the tool to misbehave, else None."""
    q = (program or "").strip()
    if not q:
        return {"status": "REFUSED", "reason": "empty query", "scope_limit": SCOPE}
    # a bare gene symbol, rather than a program name
    if _GENE_LIKE.match(q.upper()) and not q.upper().startswith(("HALLMARK_", "REACTOME_", "GOBP_",
                                                 "KEGG_", "WP_", "BIOCARTA_")):
        return {"status": "REFUSED", "query": q, "reason": REFUSAL,
                "scope_limit": SCOPE}
    # asking for a ranking / candidate list
    if any(w in q.lower() for w in ("top ", "best ", "rank", "candidate",
                                    "nominate", "most promising", "which gene")):
        return {"status": "REFUSED", "query": q, "reason": NO_NOMINATION,
                "scope_limit": SCOPE}
    return None
