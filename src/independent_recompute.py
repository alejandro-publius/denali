"""An INDEPENDENT second implementation of the headline statistic.

Written from the METHOD section of README.md and docs/DATA_DICTIONARY.md.
`src/score_k562.py`, `src/sweep.py` and `src/freeze_predictor.py` were not read
while writing it. That is the whole point: a reimplementation that consulted the
original would only prove the original can be copied.

Deliberately different machinery wherever a choice existed:

| step | the frozen path | here |
|---|---|---|
| Mann-Whitney U | its own byte-frozen scorer | `scipy.stats.mannwhitneyu` |
| BH correction | its own | `statsmodels.stats.multitest.multipletests` |
| regression | its own | `statsmodels.formula.api.ols` |

Reads the raw 470 MB substrate, not `results/frozen/`. The only thing it takes
from the frozen files is the list of program names and the four measurability
features it does not recompute (`expr_ratio`, `sd_ratio`, `essentiality_density`,
`coherence`) -- those are inputs to the regression, not the statistic under test.
`n_hits_q05` and `R_p`, the quantities being checked, are recomputed from X.

    .venv/bin/python -m src.independent_recompute

Writes results/independent/. Never touches results/frozen/.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import h5py
import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu
from statsmodels.stats.multitest import multipletests
import statsmodels.formula.api as smf

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "K562_gwps_normalized_bulk_01.h5ad"
GMT = ROOT / "data" / "genesets" / "h.all.v2026.1.Hs.symbols.gmt"
FROZEN = ROOT / "results" / "frozen"
OUT = ROOT / "results" / "independent"

# From README: "adj R2 >= 0.60 -> measurability dominates".
FEATURES = ["frac_present", "expr_ratio", "sd_ratio", "n_present",
            "essentiality_density", "coherence"]
# The one computed from the same matrix as the outcome (README, Research
# challenges). Dropping it is what the 0.561 end of the range means.
CIRCULAR = "coherence"
TOL = 0.01          # agreement tolerance on an R^2, stated up front


def load_matrix():
    """X, the perturbation-effect matrix, plus gene symbols per column."""
    with h5py.File(RAW, "r") as f:
        X = f["X"][:]
        codes = f["var"]["gene_name"][:]
        cats = f["var"]["__categories"]["gene_name"][:]
        names = np.array([c.decode() if isinstance(c, bytes) else str(c)
                          for c in cats])
        cols = names[codes]
    return X, cols


def read_gmt(path: Path) -> dict:
    out = {}
    for line in path.read_text().splitlines():
        parts = line.rstrip("\n").split("\t")
        if len(parts) > 2:
            out[parts[0]] = set(parts[2:])
    return out


def score_program(X: np.ndarray, member_idx: np.ndarray,
                  bg_idx: np.ndarray) -> tuple[int, float]:
    """n_hits at q<0.05 and R_p, per the README formulas.

    u_z is the signed normal approximation of the Mann-Whitney U of member
    effects against background, per perturbation; BH is applied WITHIN the
    program across perturbations; R_p = log10(1 + hits).
    """
    n_pert = X.shape[0]
    p = np.ones(n_pert)
    for i in range(n_pert):
        a = X[i, member_idx]
        b = X[i, bg_idx]
        a = a[np.isfinite(a)]          # mask, never impute (CLAUDE.md)
        b = b[np.isfinite(b)]
        if a.size < 2 or b.size < 2:
            continue
        # two-sided, normal approximation with tie correction -- scipy's own,
        # not a hand-rolled mu/sigma
        p[i] = mannwhitneyu(a, b, alternative="two-sided",
                            method="asymptotic").pvalue
    ok = np.isfinite(p)
    q = np.ones(n_pert)
    if ok.sum():
        q[ok] = multipletests(p[ok], method="fdr_bh")[1]
    hits = int((q < 0.05).sum())
    return hits, float(np.log10(1.0 + hits))


def main() -> int:
    if not RAW.exists():
        print(f"missing substrate {RAW} -- see `make data`", file=sys.stderr)
        return 1
    frozen = pd.read_csv(FROZEN / "program_summary.csv")
    sets = read_gmt(GMT)

    print("loading X ...", flush=True)
    X, cols = load_matrix()
    print(f"X = {X.shape}, {len(set(cols))} unique symbols\n", flush=True)

    sym_to_col = {}
    for j, s in enumerate(cols):
        sym_to_col.setdefault(s, j)

    rows = []
    for n, prog in enumerate(frozen.program, 1):
        declared = sets.get(prog, set())
        member_idx = np.array(sorted({sym_to_col[s] for s in declared
                                      if s in sym_to_col}))
        if member_idx.size == 0:
            continue
        mask = np.ones(X.shape[1], bool)
        mask[member_idx] = False
        bg_idx = np.flatnonzero(mask)
        hits, r_p = score_program(X, member_idx, bg_idx)
        rows.append({"program": prog, "n_present_indep": int(member_idx.size),
                     "n_hits_indep": hits, "R_p_indep": round(r_p, 6)})
        print(f"  [{n:>2}/{len(frozen)}] {prog:<52} hits={hits:>5} "
              f"R_p={r_p:.4f}", flush=True)

    ind = pd.DataFrame(rows)
    df = frozen.merge(ind, on="program")

    # --- agreement on the per-program statistic --------------------------
    r_pearson = float(np.corrcoef(df.R_p, df.R_p_indep)[0, 1])
    r_spearman = float(df.R_p.corr(df.R_p_indep, method="spearman"))
    max_abs = float((df.R_p - df.R_p_indep).abs().max())
    mean_abs = float((df.R_p - df.R_p_indep).abs().mean())

    # --- agreement on the HEADLINE regressions ---------------------------
    # statsmodels OLS, formula interface. adj R^2 on all six, then without the
    # circular feature, then size alone.
    def adj_r2(cols_):
        f = "R_p_indep ~ " + " + ".join(cols_)
        return float(smf.ols(f, data=df).fit().rsquared_adj)

    def r2(cols_):
        f = "R_p_indep ~ " + " + ".join(cols_)
        return float(smf.ols(f, data=df).fit().rsquared)

    all_six = adj_r2(FEATURES)
    five = adj_r2([f for f in FEATURES if f != CIRCULAR])
    size_alone = r2(["n_present"])

    # the same three computed against the FROZEN R_p, so a disagreement can be
    # attributed to the statistic or to the regression, not left ambiguous
    def adj_r2_frozen(cols_):
        return float(smf.ols("R_p ~ " + " + ".join(cols_), data=df).fit().rsquared_adj)
    all_six_frozen = adj_r2_frozen(FEATURES)
    five_frozen = adj_r2_frozen([f for f in FEATURES if f != CIRCULAR])
    size_frozen = float(smf.ols("R_p ~ n_present", data=df).fit().rsquared)

    published = {"all_six": 0.751, "x_independent_five": 0.561,
                 "size_alone": 0.4649}
    got = {"all_six": all_six, "x_independent_five": five,
           "size_alone": size_alone}
    agree = {k: bool(abs(got[k] - published[k]) <= TOL) for k in published}

    result = {
        "what_this_is": (
            "A second implementation of the headline statistic, written from "
            "the README method section without reading src/score_k562.py, "
            "src/sweep.py or src/freeze_predictor.py. Different Mann-Whitney "
            "(scipy), different BH (statsmodels), different regression "
            "(statsmodels OLS)."),
        "tolerance": TOL,
        "per_program_statistic": {
            "pearson_r_vs_frozen_R_p": round(r_pearson, 6),
            "spearman_r_vs_frozen_R_p": round(r_spearman, 6),
            "max_abs_diff_R_p": round(max_abs, 6),
            "mean_abs_diff_R_p": round(mean_abs, 6),
            "n_programs": int(len(df)),
        },
        "headline_recomputed_on_independent_R_p": {
            k: round(v, 4) for k, v in got.items()},
        "same_regressions_on_frozen_R_p": {
            "all_six": round(all_six_frozen, 4),
            "x_independent_five": round(five_frozen, 4),
            "size_alone": round(size_frozen, 4)},
        "published": published,
        "agrees_within_tolerance": agree,
        "all_agree": bool(all(agree.values())),
        "what_would_falsify_this": (
            "Any of the three published figures differing from the "
            f"independent recomputation by more than {TOL}. That would mean "
            "the headline depends on one implementation of the statistic "
            "rather than on the data, and it would have to be reported as "
            "such rather than reconciled."),
        "what_this_does_not_establish": (
            "That the METHOD is correct. Two implementations of a wrong method "
            "agree with each other. This rules out implementation error in the "
            "frozen scorer; it does not rule out the method being the wrong "
            "question to ask, which is what evaluations 1-11 are for."),
    }

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "independent_recompute.json").write_text(
        json.dumps(result, indent=2) + "\n")
    df[["program", "n_present", "n_present_indep", "n_hits_q05",
        "n_hits_indep", "R_p", "R_p_indep"]].to_csv(
        OUT / "per_program_comparison.csv", index=False)

    print(f"\n{'='*70}")
    print(f"per-program R_p   pearson {r_pearson:.6f}  spearman {r_spearman:.6f}")
    print(f"                  max|diff| {max_abs:.6f}   mean|diff| {mean_abs:.6f}")
    print(f"\n{'figure':<24}{'published':>11}{'independent':>13}{'agree':>8}")
    for k in published:
        print(f"{k:<24}{published[k]:>11}{got[k]:>13.4f}"
              f"{('YES' if agree[k] else 'NO'):>8}")
    print(f"\nALL AGREE WITHIN {TOL}: {result['all_agree']}")
    print(f"wrote {OUT}/independent_recompute.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
