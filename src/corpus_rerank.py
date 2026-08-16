"""In the median published screen, how many of the top 10 survive the size correction?

POST-HOC, exploratory. Nothing pre-registered. This arm extends the corpus audit
(src/corpus_audit.py, docs/CORPUS.md): that arm measured how much of each published
screen's set-level ranking is predicted by set size alone; this one applies the
packaged correction to the same screens and counts what survives it.

WHAT IS APPLIED. `denali_audit.core.rerank`, imported from packages/denali-audit --
the vendored code path the tool ships, not a reimplementation. Per screen: original
rank = hits-per-set descending, corrected rank = residual of log10(1+hits) regressed
on raw set size, survivors = sets in the top 10 of both. `names=None`, so no set is
named in anything this writes.

EVERY ANALYSIS DECISION, FIXED BEFORE ANY VALUE WAS COMPUTED:
  substrate   BioGRID ORCS 2.0.18 (the pinned release, not Latest), same file layout
  inclusion   identical to corpus_audit: >= 20 hits, >= 10,000 genes measured,
              >= 8 usable sets (usable = >= 5 measured members)
  top N       10, the number of candidates the study's own framing uses
  survivors   `survived_top_n` from the packaged rerank(), verbatim
  strata      the same four hit-list-size bins as corpus_audit
  collapse    publications collapsed to their median screen, same as corpus_audit

SANITY GATES -- this script writes NOTHING unless both hold:
  1. JOIN GATE. The audited screens must match results/corpus/corpus_per_screen.csv
     row-for-row, and the per-screen size-alone R^2 recomputed here must equal the
     committed value for every screen. If the join drifts, everything downstream
     is noise and the script aborts.
  2. OWN-SCREEN GATE. denali's own screen (the g:Profiler-shaped export the judge
     check runs, read through the same adapters) must land at or above the corpus
     90th percentile on size-alone R^2, matching the corpus audit -- and its own
     rerank must reproduce the published 3-of-10.

THE ESTIMAND, PRECISELY. The ranking corrected here is the naive hits-per-set
ordering -- the same construction the corpus audit's R^2 measures -- not any
publication's own enrichment ranking, which ORCS does not carry. Survivorship of a
p-value-ranked list is a different (and unmeasured) quantity. Hit counts tie often
in small hit lists, and the packaged rerank breaks ties by input order (Hallmark
file order, deterministic); the share of screens whose top-10 boundary sits on a
tie is reported so nobody has to trust that this does not matter.

    .venv/bin/python -m src.corpus_rerank

Reads data/raw/orcs/ (docs/CORPUS.md documents the download) and
data/genesets/h.all.v2026.1.Hs.symbols.gmt, plus results/corpus/ for the join gate.
Writes results/corpus_rerank/corpus_rerank.json and corpus_rerank_per_screen.csv.
Names no screen, no publication and no gene set: the unit of inference is the
distribution. results/frozen/ is untouched by this arm.
"""
from __future__ import annotations

import glob
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

# src/__init__.py puts the vendored packages/denali-audit on the path.
from denali_audit.adapters import detect            # noqa: E402
from denali_audit.core import audit, rerank         # noqa: E402

from src.corpus_audit import GMT, RAW, load_gmt, r2  # noqa: E402

OUTDIR = ROOT / "results" / "corpus_rerank"
COMMITTED = ROOT / "results" / "corpus" / "corpus_per_screen.csv"
OWN = ROOT / "examples" / "example_gprofiler.csv"
TOP = 10
BINS = [(20, 100), (100, 500), (500, 2000), (2000, 10**9)]


def quantiles(s: pd.Series) -> dict:
    q = s.quantile([0.10, 0.25, 0.50, 0.75, 0.90])
    return {f"p{int(k * 100)}": round(float(v), 2) for k, v in q.items()}


def main() -> int:
    sets = load_gmt(ROOT / GMT)
    print(f"{len(sets)} Hallmark sets loaded")

    committed = pd.read_csv(COMMITTED, dtype={"screen_id": str})

    rows = []
    n_parse_failed = n_excluded = 0
    files = sorted(glob.glob(str(ROOT / RAW / "*screen.tab.txt")))
    for i, f in enumerate(files):
        if i % 400 == 0:
            print(f"  {i}/{len(files)}")
        # Parsing and inclusion are corpus_audit's, verbatim: same columns, same
        # thresholds, same accounting. A screen lands in exactly one bucket.
        try:
            d = pd.read_csv(f, sep="\t", usecols=["#SCREEN_ID", "OFFICIAL_SYMBOL", "HIT"],
                            low_memory=False)
        except Exception:
            n_parse_failed += 1
            continue
        sid = str(d["#SCREEN_ID"].iloc[0]) if len(d) else None
        if sid is None:
            n_parse_failed += 1
            continue
        hits = set(d.loc[d.HIT.astype(str).str.upper() == "YES", "OFFICIAL_SYMBOL"].dropna())
        measured = set(d.OFFICIAL_SYMBOL.dropna())
        if len(hits) < 20 or len(measured) < 10000:
            n_excluded += 1
            continue
        size, nhit = [], []
        for g in sets.values():
            m = g & measured
            if len(m) < 5:
                continue
            size.append(len(m))
            nhit.append(len(g & hits))
        if len(size) < 8:
            n_excluded += 1
            continue
        v = r2(np.log10(np.array(size)), np.log10(1 + np.array(nhit)))
        if not np.isfinite(v):
            n_excluded += 1
            continue

        rr = rerank(size, nhit, names=None, top=TOP)
        h_desc = sorted(nhit, reverse=True)
        rows.append({
            "screen_id": sid,
            "survivors_top10": rr["survived_top_n"],
            "top10_boundary_tied": bool(len(h_desc) > TOP and h_desc[TOP - 1] == h_desc[TOP]),
            "r2_size_alone": round(v, 4),
        })

    R = pd.DataFrame(rows)
    print(f"\nfiles: {len(files)}  parse-failed: {n_parse_failed}  "
          f"excluded by rule: {n_excluded}  audited: {len(R)}")

    # ---- gate 1: the join ----
    merged = R.merge(committed, on="screen_id", suffixes=("", "_committed"))
    same_ids = len(merged) == len(R) == len(committed)
    max_dr2 = float((merged.r2_size_alone - merged.r2_size_alone_committed).abs().max()) \
        if same_ids else float("inf")
    if not same_ids or max_dr2 > 1e-6:
        print(f"JOIN GATE FAILED: ids match={same_ids}, max |dR2|={max_dr2}. "
              f"Nothing written.")
        return 1
    print(f"join gate: {len(merged)} screens match evaluation 10 row-for-row, "
          f"max |dR2| = {max_dr2}")
    R = merged[["screen_id", "survivors_top10", "top10_boundary_tied", "r2_size_alone",
                "n_hits", "n_measured", "n_sets_used", "source_id", "cell_line",
                "phenotype", "library"]]

    # ---- gate 2: our own screen, through the same packaged code path ----
    own_df = pd.read_csv(OWN)
    m = detect(own_df)
    own_audit = audit(m.size, m.hits)
    own_rr = rerank(m.size, m.hits, names=None, top=TOP)
    p90 = float(R.r2_size_alone.quantile(0.90))
    own_r2 = own_audit["r2_size_alone"]
    print(f"own screen: R2 {own_r2} vs corpus p90 {p90:.4f}; "
          f"survivors {own_rr['survived_top_n']}/{TOP}")
    if own_r2 < p90 or own_rr["survived_top_n"] != 3:
        print("OWN-SCREEN GATE FAILED: expected R2 >= corpus p90 and 3/10 survivors. "
              "Nothing written.")
        return 1

    # ---- the distribution ----
    surv = R.survivors_top10
    n_zero, n_all = int((surv == 0).sum()), int((surv == TOP).sum())
    print(f"\nsurvivors of the top {TOP} across {len(R)} published screens:")
    for k, v in quantiles(surv).items():
        print(f"  {k}  {v}")
    print(f"  mean {surv.mean():.2f}")
    print(f"  zero survivors: {n_zero} screens ({100 * n_zero / len(R):.1f}%)")
    print(f"  all ten hold:   {n_all} screens ({100 * n_all / len(R):.1f}%)")

    strat = []
    for lo, hi in BINS:
        s = R[(R.n_hits >= lo) & (R.n_hits < hi)]
        if len(s) < 5:
            continue
        strat.append({"bin": f"{lo}-{hi if hi < 10**9 else 'inf'}", "n": int(len(s)),
                      "median_survivors": round(float(s.survivors_top10.median()), 1),
                      "median_r2": round(float(s.r2_size_alone.median()), 4)})
        print(f"  {strat[-1]['bin']:>12s}  n={len(s):4d}  "
              f"median survivors = {strat[-1]['median_survivors']}")

    pub = R.groupby("source_id").survivors_top10.median()
    print(f"\npublication-level (each publication collapsed to its median screen, "
          f"n={len(pub)}):")
    for k, v in quantiles(pub).items():
        print(f"  {k}  {v}")

    untied = R[~R.top10_boundary_tied]
    tie_share = 100 * float(R.top10_boundary_tied.mean())
    rho = float(pd.Series(R.r2_size_alone).corr(pd.Series(surv.astype(float)),
                                                method="spearman"))
    print(f"\ntop-10 boundary sits on a tied hit count in {tie_share:.1f}% of screens; "
          f"median survivors among untied screens: {untied.survivors_top10.median():.1f}")
    print(f"spearman(size-alone R2, survivors) = {rho:.3f}")

    report = {
        "status": "POST-HOC, exploratory. Not pre-registered.",
        "question": f"Of each published screen's top {TOP} sets (ranked by hits per "
                    f"set), how many keep a top-{TOP} place once set size is "
                    f"regressed out?",
        "correction": "denali_audit.core.rerank, the packaged code path, verbatim: "
                      "log10(1+hits) regressed on set size; ranked by residual",
        "estimand_warning": "The ranking corrected here is the naive hits-per-set "
                            "ordering, the same construction evaluation 10's R^2 "
                            "measures -- NOT any publication's own enrichment "
                            "ranking, which ORCS does not carry. The rerank "
                            "residualises RAW set size (the packaged tool's "
                            "correction); evaluation 10's headline R^2 uses log "
                            "size. Neither substitutes for the other.",
        "source": "BioGRID ORCS 2.0.18, human, MIT licence. 1,952 screens / 418 publications.",
        "gene_sets": "MSigDB Hallmark v2026.1.Hs, 50 sets",
        "inclusion": "identical to evaluation 10: HIT=YES count >= 20 and >= 10,000 "
                     "genes measured; >= 8 usable sets (>= 5 measured members)",
        "n_screen_files": int(len(files)),
        "n_parse_failed": int(n_parse_failed),
        "n_excluded_by_rule": int(n_excluded),
        "n_screens_audited": int(len(R)),
        "sanity_gates": {
            "join": {"screens_matched_row_for_row": int(len(R)),
                     "max_abs_r2_delta_vs_committed": max_dr2},
            "own_screen": {"r2_size_alone": own_r2,
                           "corpus_p90": round(p90, 4),
                           "above_p90": bool(own_r2 >= p90),
                           "survivors_top10": int(own_rr["survived_top_n"]),
                           "matches_published_3_of_10": True},
        },
        "quantiles": quantiles(surv),
        "mean": round(float(surv.mean()), 2),
        "n_zero_survivors": n_zero,
        "pct_zero_survivors": round(100 * n_zero / len(R), 1),
        "n_all_ten_hold": n_all,
        "pct_all_ten_hold": round(100 * n_all / len(R), 1),
        "stratified_by_hitlist_size": strat,
        "publication_level_pseudo_replication": {
            "why": "Same correction as evaluation 10: one publication contributes "
                   "up to hundreds of screens, so each is collapsed to its median "
                   "screen before quantiles. Reported alongside the screen-level "
                   "figures, never instead of them.",
            "n_publications": int(len(pub)),
            "quantiles": quantiles(pub),
            "median": round(float(pub.median()), 1),
        },
        "tie_sensitivity": {
            "why": "Hit counts tie, and the packaged rerank breaks ties by input "
                   "order. Screens whose top-10 boundary sits on a tie are the "
                   "ones where that arbitrary choice could move the count.",
            "pct_screens_with_tied_top10_boundary": round(tie_share, 1),
            "median_survivors_untied_screens_only":
                round(float(untied.survivors_top10.median()), 1),
            "n_untied": int(len(untied)),
        },
        "spearman_r2_vs_survivors": round(rho, 3),
    }
    OUTDIR.mkdir(parents=True, exist_ok=True)
    (OUTDIR / "corpus_rerank.json").write_text(json.dumps(report, indent=2) + "\n")
    R.to_csv(OUTDIR / "corpus_rerank_per_screen.csv", index=False)
    print(f"\nwrote {OUTDIR}/corpus_rerank.json and {OUTDIR}/corpus_rerank_per_screen.csv")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
