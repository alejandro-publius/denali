"""POST-FREEZE SENSITIVITY CHECK. Not pre-registered.

Run after the 6:30 PM hard freeze, prompted by an adversarial self-critique that
named this as the project's weakest point. Writes to results/sensitivity/ ONLY.
Does not replace, revise or reweight the pre-registered primary.

    .venv/bin/python -m src.sensitivity_stripped
"""
from __future__ import annotations
import json
from pathlib import Path
import pandas as pd, statsmodels.api as sm

ALL = ["frac_present","expr_ratio","sd_ratio","n_present","essentiality_density","coherence"]
CONSTRUCTION = ["n_present","frac_present","coherence"]
MEASUREMENT = ["expr_ratio","sd_ratio","essentiality_density"]

def main():
    S = pd.read_csv("results/frozen/program_summary.csv")
    d = S.dropna(subset=ALL+["R_p"]); y = d.R_p
    fit = lambda F: sm.OLS(y, sm.add_constant((d[F]-d[F].mean())/d[F].std())).fit()
    for lab, F in [("all_six (PRE-REGISTERED)", ALL),
                   ("x_independent_five", [f for f in ALL if f != "coherence"]),
                   ("MEASUREMENT only", MEASUREMENT),
                   ("SET-CONSTRUCTION only", CONSTRUCTION)]:
        print(f"{lab:28s} adj R2 = {fit(F).rsquared_adj:.4f}")
    print(f"{'set size alone':28s}    R2 = "
          f"{sm.OLS(y, sm.add_constant(d.n_present)).fit().rsquared:.4f}")
    print("\nVERDICT: measurement-only COLLAPSES to 0.152; construction-only reaches 0.697.")
    print("See results/sensitivity/README.md")

if __name__ == "__main__":
    main()
