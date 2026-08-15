"""Tier 3 — freeze the predictor. RUN BEFORE THE HELD OUT TEN ARE OPENED.

Serialises the OLS exactly as fit on the 50 Hallmark programs, together with
every decision rule needed to evaluate the held-out set. Once this file is
hashed and committed, nothing in it may change.

    .venv/bin/python -m src.freeze_predictor
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm

FROZEN = Path("results/frozen")
OUT = FROZEN / "predictor.json"
FEATURES = ["frac_present", "expr_ratio", "sd_ratio", "n_present",
            "essentiality_density", "coherence"]
X_INDEP = [f for f in FEATURES if f != "coherence"]

# Binary rule, fixed here BEFORE the held-out set is opened.
# Matches program_summary.reversibility_call: reversible iff >=100 hits.
REVERSIBLE_MIN_HITS = 100
REVERSIBLE_MIN_RP = float(np.log10(1 + REVERSIBLE_MIN_HITS))

# Gate C1 criteria, unchanged
GATE = {"min_frac_present": 0.50, "min_n_present": 25,
        "min_expr_ratio": 1.0, "min_sd_ratio": 1.0}


def main() -> None:
    S = pd.read_csv(FROZEN / "program_summary.csv")
    d = S.dropna(subset=FEATURES + ["R_p"])
    mu, sd = d[FEATURES].mean(), d[FEATURES].std()
    X = sm.add_constant((d[FEATURES] - mu) / sd)
    m = sm.OLS(d.R_p, X).fit()
    resid_sd = float((d.R_p - m.predict(X)).std())

    Xi = sm.add_constant((d[X_INDEP] - d[X_INDEP].mean()) / d[X_INDEP].std())
    mi = sm.OLS(d.R_p, Xi).fit()

    pred = {
        "model": "OLS, R_p ~ 6 standardised measurability features",
        "fit_on": "50 MSigDB Hallmark programs (includes programs A and B; disclosed)",
        "n_train": int(len(d)),
        "features": FEATURES,
        "standardisation": {"mean": {k: float(v) for k, v in mu.items()},
                            "std": {k: float(v) for k, v in sd.items()}},
        "coefficients": {k: float(v) for k, v in m.params.items()},
        "adjusted_r2_all_six": round(float(m.rsquared_adj), 4),
        "adjusted_r2_x_independent_only": round(float(mi.rsquared_adj), 4),
        "residual_sd": round(resid_sd, 4),
        "coherence_circularity": (
            "coherence is derived from the same matrix X as R_p, so part of the "
            "all-six fit is mechanical. Honest range is 0.561 to 0.751."),
        "binary_rule": {
            "reversible_iff_hits_at_least": REVERSIBLE_MIN_HITS,
            "reversible_iff_predicted_R_p_at_least": round(REVERSIBLE_MIN_RP, 4),
        },
        "gate_criteria": GATE,
        "heldout_thresholds_from_prereg_f": {
            "axis1_spearman": {"success": ">=0.60", "partial": "0.30-0.60",
                               "failure": "<0.30", "failure_inverted": "<0"},
            "axis2_balanced_accuracy": {"success": ">=0.75", "partial": "0.55-0.75",
                                        "failure": "<0.55"},
            "underpowered_if": "fewer than 8 of 10 held-out programs pass the gate",
            "on_failure": "report it; do NOT refit, re-feature, re-threshold or re-draw",
        },
        "frozen_before_heldout_opened": True,
    }
    OUT.write_text(json.dumps(pred, indent=2, sort_keys=True))
    h = hashlib.sha256(OUT.read_bytes()).hexdigest()
    print(f"PREDICTOR FROZEN -> {OUT}")
    print(f"sha256: {h}")
    print(f"  adj R2 all six       : {pred['adjusted_r2_all_six']}")
    print(f"  adj R2 X-independent : {pred['adjusted_r2_x_independent_only']}")
    print(f"  residual SD          : {pred['residual_sd']}")
    print(f"  reversible iff R_p >= {pred['binary_rule']['reversible_iff_predicted_R_p_at_least']}")
    print("\nHELD OUT TEN NOT YET OPENED.")


if __name__ == "__main__":
    main()
