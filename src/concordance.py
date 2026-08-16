"""How much do two independent screens of the same programs agree?

POST-FREEZE. Not pre-registered. Prompted by our own landscape review, which
found this question unanswered in the literature we could reach and noted that
we had no right to claim a number for it. We have two independently screened
cell lines, so we can stop guessing.

The question a biologist actually has: **if I ran this screen twice, in two cell
lines, how much of my hit list would survive?** That is the number that decides
whether a ranking is worth a year of validation, and it is the one nobody quotes.

Three things are measured, all on the 50 Hallmark programs scored identically in
K562 and RPE1 by the byte-frozen scorer:

  1. rank agreement between the two screens (Spearman)
  2. top-k overlap -- of the k programs each screen calls most reversible, how
     many are the same programs
  3. how much of the agreement is explained by SET SIZE rather than by biology,
     which is the whole point of this project applied to concordance itself

Point 3 is the one that matters. Two screens agreeing is only evidence of biology
if they agree for reasons other than both being confounded the same way.

Writes results/concordance/ ONLY.

    .venv/bin/python -m src.concordance
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy.stats import spearmanr

FROZEN = Path("results/frozen")
RPE1 = Path("results/rpe1")
OUT = Path("results/concordance")


def top_k_overlap(a: pd.Series, b: pd.Series, k: int) -> float:
    """Fraction of the top k that both screens agree on."""
    return len(set(a.nlargest(k).index) & set(b.nlargest(k).index)) / k


def main() -> None:
    K = pd.read_csv(FROZEN / "program_summary.csv")
    R = pd.read_csv(RPE1 / "program_summary_rpe1.csv")
    m = K[["program", "R_p", "n_hits_q05", "n_present"]].merge(
        R[["program", "R_p", "n_hits_q05", "n_present"]],
        on="program", suffixes=("_k562", "_rpe1")).dropna(subset=["R_p_rpe1"])

    kp = m.set_index("program").R_p_k562
    rp = m.set_index("program").R_p_rpe1

    rho, p_rho = spearmanr(kp, rp)
    overlaps = {f"top_{k}": round(top_k_overlap(kp, rp, k), 3)
                for k in (5, 10, 20)}

    # --- the part that matters -------------------------------------------
    # Both screens are confounded by set size. If size explains the agreement,
    # then "it replicated" means "it was big in both", not "it is real".
    size = m.n_present_k562
    r2_k = sm.OLS(kp.values, sm.add_constant(size)).fit().rsquared
    r2_r = sm.OLS(rp.values, sm.add_constant(size)).fit().rsquared

    # partial Spearman: rank-correlate the residuals after removing size
    res_k = sm.OLS(kp.values, sm.add_constant(size)).fit().resid
    res_r = sm.OLS(rp.values, sm.add_constant(size)).fit().resid
    rho_partial, p_partial = spearmanr(res_k, res_r)

    # top-k overlap expected by chance, and by size alone
    n = len(m)
    chance = {f"top_{k}": round(k / n, 3) for k in (5, 10, 20)}
    size_rank = m.set_index("program").n_present_k562
    size_only = {f"top_{k}": round(top_k_overlap(size_rank, rp, k), 3)
                 for k in (5, 10, 20)}

    res = {
        "question": ("If you ran the same 50-program analysis on two independently "
                     "screened cell lines, how much of the ranking would agree -- "
                     "and how much of that agreement is set size rather than biology?"),
        "n_programs": int(n),
        "screens": ["K562 (9,837 targets)", "RPE1 (2,386 targets)"],
        "raw_agreement": {
            "spearman_rho": round(float(rho), 4),
            "p": float(f"{p_rho:.4g}"),
            "top_k_overlap": overlaps,
            "top_k_overlap_expected_by_chance": chance,
        },
        "how_much_is_size": {
            "size_explains_in_k562_r2": round(float(r2_k), 4),
            "size_explains_in_rpe1_r2": round(float(r2_r), 4),
            "spearman_after_removing_size": round(float(rho_partial), 4),
            "p_after_removing_size": float(f"{p_partial:.4g}"),
            "agreement_lost_to_size": round(float(rho - rho_partial), 4),
            "top_k_overlap_using_SIZE_ALONE_to_predict_rpe1": size_only,
        },
        "reading": (
            f"Raw rank agreement between two independent screens is rho "
            f"{rho:+.3f}. After removing set size from both, it falls to "
            f"{rho_partial:+.3f}. So {abs(rho - rho_partial) / abs(rho):.0%} of the "
            f"apparent cross-screen reproducibility is explained by how the gene "
            f"sets were built, not by the biology being reproducible."),
        "why_it_matters": (
            "'It replicated in a second cell line' is the strongest evidence most "
            "hit lists ever get. This measures how much of that evidence is "
            "carried by set size -- a property of the annotation, not the "
            "experiment. Both screens are confounded the same way, so agreeing "
            "for the same wrong reason looks exactly like agreeing for the right "
            "one."),
        "limits": (
            "50 programs, two cell lines, one lab, one assay. RPE1 covers 24.3% of "
            "K562's targets and that subset is disproportionately essential genes "
            "(rpe1_coverage_collision, FAIL). This is a measurement on our own two "
            "screens and not a general estimate of cross-screen reproducibility."),
        "status": "POST-FREEZE, NOT PRE-REGISTERED",
        "prompted_by": "our own landscape review finding the question unanswered",
    }

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "cross_screen.json").write_text(json.dumps(res, indent=2) + "\n")
    m.to_csv(OUT / "paired_programs.csv", index=False)

    print("CROSS-SCREEN CONCORDANCE (post-freeze, not pre-registered)")
    print(f"  programs paired            : {n}")
    print(f"  raw Spearman               : {rho:+.4f}  p={p_rho:.3g}")
    print(f"  after removing set size    : {rho_partial:+.4f}  p={p_partial:.3g}")
    print(f"  agreement lost to size     : {rho - rho_partial:+.4f}  "
          f"({abs(rho - rho_partial) / abs(rho):.0%} of it)")
    print(f"  top-10 overlap             : {overlaps['top_10']}  "
          f"(chance {chance['top_10']}, size alone {size_only['top_10']})")
    print(f"wrote {OUT}/")


if __name__ == "__main__":
    main()
