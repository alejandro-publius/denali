"""The check the breadth probe existed to make, and the one it nearly shipped without.

POST-HOC, EXPLORATORY. Not pre-registered.

audit() answers "how much of this ranking is predicted by set size alone?". That number
is only interpretable against the value it would take WITH NO BIOLOGY AT ALL, and the
no-biology value is not zero. It depends on how `hits` was defined:

  COUNTING STRUCTURE  -- hits are drawn from the set's own members, so hits <= size.
      This is what classical overlap enrichment does: "how many of this set's members
      came back significant". Under a constant, size-independent per-member hit rate p,
      hits ~ Binomial(size, p), and R2 of log10(1+hits) on size is LARGE by construction.
      The correct null is that binomial.

  NO COUNTING STRUCTURE -- hits are counted over some other universe entirely, so hits
      is not bounded by size. denali's own primary is this shape: `hits` counts
      PERTURBATIONS (out of 9,837) that move a program, not members of the program.
      Under no biology, size and hits are independent, and R2 is ~0. The correct null
      is a permutation.

Regressing a count on the number of trials that produced it recovers the trial count.
That is arithmetic. A high R2 in a counting-structure analysis is therefore not by
itself evidence of a confound, and reporting it as one would be the exact error this
tool exists to detect -- the same error its own off-target arm caught and refused when
a tautological regression returned R2 = 1.0000.

    python -m results.breadth.null_baselines      # or run directly

Writes results/breadth/null_baselines.json. Names no set, pathway, gene or region.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from denali_audit import audit                                        # noqa: E402

OUT = ROOT / "results" / "breadth" / "null_baselines.json"
SEED = 20260816
N_ITER = 300


def _r2(size, hits) -> float:
    return audit(size, hits)["r2_size_alone"]


def null_baseline(size, hits, n_iter: int = N_ITER, seed: int = SEED) -> dict:
    """Observed R2 against the correct no-biology null for this mapping's structure."""
    rng = np.random.default_rng(seed)
    size = np.asarray(size, dtype=float)
    hits = np.asarray(hits, dtype=float)
    ok = np.isfinite(size) & np.isfinite(hits)
    size, hits = size[ok], hits[ok]
    if len(size) < 8:
        return {"n_sets": int(len(size)), "note": "fewer than 8 sets; audit() refuses"}

    obs = _r2(size, hits)
    rate = float(hits.sum() / size.sum()) if size.sum() else float("nan")
    counting = bool(np.all(hits <= size)) and 0.0 <= rate <= 1.0

    draws = []
    for _ in range(n_iter):
        sim = (rng.binomial(size.astype(int), rate) if counting
               else rng.permutation(hits))
        try:
            v = _r2(size, sim)
        except Exception:
            continue
        if np.isfinite(v):
            draws.append(v)
    draws = np.asarray(draws, dtype=float)
    lo, hi = (float(np.percentile(draws, 2.5)), float(np.percentile(draws, 97.5))) \
        if len(draws) else (float("nan"), float("nan"))

    return {
        "n_sets": int(len(size)),
        "observed_r2": round(float(obs), 4),
        "null_kind": "binomial constant-rate (hits drawn from the set's own members)"
                     if counting else "permutation (hits not bounded by size)",
        "has_counting_structure": counting,
        "frac_hits_le_size": round(float((hits <= size).mean()), 4),
        "null_mean_r2": round(float(draws.mean()), 4) if len(draws) else None,
        "null_ci95": [round(lo, 4), round(hi, 4)] if len(draws) else None,
        "observed_minus_null": round(float(obs - draws.mean()), 4) if len(draws) else None,
        "position": ("ABOVE null" if len(draws) and obs > hi else
                     "BELOW null" if len(draws) and obs < lo else "INSIDE null band"),
    }


def main() -> int:
    report = {
        "status": "POST-HOC, exploratory. Not pre-registered.",
        "what_this_measures": (
            "The value audit()'s R2 would take with no biology at all, at the same set "
            "sizes and the same overall hit rate. An observed R2 is only interpretable "
            "against it."),
        "why": (
            "Where hits are drawn from the set's own members (classical overlap "
            "enrichment), regressing a count on the number of trials that produced it "
            "recovers the trial count. A large R2 is then arithmetic, not a confound."),
        "arms": {},
    }

    # denali's own primary -- the published 0.4649. hits counts PERTURBATIONS, not
    # members, so this mapping has no counting structure and takes a permutation null.
    frozen = ROOT / "results" / "frozen" / "program_summary.csv"
    if frozen.exists():
        S = pd.read_csv(frozen)
        report["arms"]["denali_primary_published_0.4649"] = null_baseline(
            S.n_present, S.n_hits_q05)

    # metabolite sets
    met = ROOT / "results" / "breadth" / "metabolites" / "sets_standardized.csv"
    if met.exists():
        M = pd.read_csv(met)
        for mapping, g in M.groupby("mapping"):
            if len(g) >= 8:
                report["arms"][f"metabolites :: {mapping}"] = null_baseline(
                    g["size"], g["hits"])

    # microbiome functional sets
    mic = ROOT / "results" / "breadth" / "microbiome"
    if (mic / "table_D_members_measured.tsv").exists():
        D = pd.read_csv(mic / "table_D_members_measured.tsv", sep="\t")
        for cohort, g in D.groupby("cohort"):
            report["arms"][f"microbiome :: members-measured FDR10 :: {cohort}"] = \
                null_baseline(g["size_members_measured"], g["hits_FDR10"])
    if (mic / "table_A_detection.tsv").exists():
        A = pd.read_csv(mic / "table_A_detection.tsv", sep="\t")
        for cohort, g in A.groupby("cohort"):
            report["arms"][f"microbiome :: detection :: {cohort}"] = \
                null_baseline(g["size"], g["hits"])

    # region sets: paired real-query vs matched control, per job
    reg = ROOT / "results" / "breadth" / "regions" / "set_size_hits.csv.gz"
    if reg.exists():
        df = pd.read_csv(reg)
        rows = []
        for job, g in df.groupby("job"):
            if len(g) < 8:
                continue
            try:
                q = _r2(g["size"], g["hits"])
                c = _r2(g["size"], g["hits_control"])
            except Exception:
                continue
            if np.isfinite(q) and np.isfinite(c):
                rows.append((q, c))
        if rows:
            R = pd.DataFrame(rows, columns=["r2_query", "r2_control"])
            report["arms"]["regions :: paired real-query vs matched control"] = {
                "n_jobs": int(len(R)),
                "median_r2_real_query": round(float(R.r2_query.median()), 4),
                "median_r2_control_set": round(float(R.r2_control.median()), 4),
                "frac_jobs_control_ge_query": round(float((R.r2_control >= R.r2_query).mean()), 4),
                "paired_median_difference": round(float((R.r2_query - R.r2_control).median()), 4),
                "null_kind": "matched empirical control (the job's own control regions, "
                             "randomised for most jobs)",
                "position": ("BELOW null" if R.r2_control.median() > R.r2_query.median()
                             else "ABOVE null"),
            }

    OUT.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    print(f"\nwrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
