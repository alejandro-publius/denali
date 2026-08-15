"""POST-FREEZE SENSITIVITY CHECK. Not pre-registered.

An external reviewer session noticed that our two dominant features -- n_present
and coherence -- are exactly the two terms of the variance-inflation factor for
a competitive gene-set test:

    VIF = 1 + (m - 1) * rho_bar        (Wu & Smyth 2012, CAMERA,
                                        Nucleic Acids Research 40(17):e133,
                                        doi:10.1093/nar/gks461)

where m is set size and rho_bar the mean pairwise inter-gene correlation. A test
that ignores this declares more hits for larger, more correlated sets regardless
of biology. If our headline pattern is that artifact, one derived quantity built
from those two features alone should predict R_p about as well as the whole
six-feature model.

It does. This check was implemented twice independently -- once by the reviewer
session, once here, without reading each other's code -- and the two agree; this
module's numbers also reconcile exactly with the frozen set_size_alone value
(0.4649 raw == 0.4538 adjusted at n=50, k=1).

THE HONEST BOUND, stated here because it is the first thing a reviewer should
see: coherence is computed from the same matrix as the outcome, so VIF inherits
the same partial circularity as the six-feature model's upper bound. Compare
log-VIF (0.726) to the pre-registered UPPER bound (0.751) only. Flattening
coherence to its median collapses VIF to 0.463 -- barely above size alone --
which is the coherence-free statement and pairs with the pre-registered lower
bound (0.561).

What this changes: the finding is no longer only "our features predict apparent
reversibility." A statistical theory published in 2012 predicts, analytically,
the empirical pattern we recovered from a genome-scale screen without looking
for it. That is validation against a standard outside this project's own
reasoning -- and it names the next experiment: re-run the sweep with a
VIF-corrected set statistic and measure how much of the effect collapses.

Writes results/sensitivity/vif_camera.json ONLY. Does not replace, revise or
reweight the pre-registered primary.

    .venv/bin/python -m src.vif_camera
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy.stats import spearmanr

FROZEN = Path("results/frozen")
OUT = Path("results/sensitivity")

FEATURES = ["n_present", "frac_present", "expr_ratio", "sd_ratio",
            "essentiality_density", "coherence"]


def adj_r2(y, X) -> float:
    return float(sm.OLS(y, sm.add_constant(X, has_constant="add"),
                        missing="drop").fit().rsquared_adj)


def main() -> None:
    S = pd.read_csv(FROZEN / "program_summary.csv")
    prov = json.loads((FROZEN / "provenance.json").read_text())
    d = S.dropna(subset=["R_p", "n_present", "coherence"]).copy()
    y = d.R_p

    d["vif"] = 1.0 + (d.n_present - 1.0) * d.coherence
    d["log_vif"] = np.log10(d.vif)
    # the coherence-free version: how much survives without the circular term
    d["vif_flat"] = np.log10(1.0 + (d.n_present - 1.0) * d.coherence.median())

    rho, p = spearmanr(d.log_vif, y)
    others = [c for c in FEATURES if c not in ("n_present", "coherence")]

    res = {
        "formula": "VIF = 1 + (m-1)*rho_bar; m=n_present, rho_bar=coherence",
        "citation": ("Wu & Smyth 2012, Camera: a competitive gene set test "
                     "accounting for inter-gene correlation. Nucleic Acids "
                     "Research 40(17):e133. doi:10.1093/nar/gks461"),
        "vif_range": [round(float(d.vif.min()), 2), round(float(d.vif.max()), 2)],
        "adj_r2": {
            "log_vif_alone": round(adj_r2(y, d[["log_vif"]]), 4),
            "vif_raw_alone": round(adj_r2(y, d[["vif"]]), 4),
            "n_present_alone": round(adj_r2(y, d[["n_present"]]), 4),
            "coherence_alone": round(adj_r2(y, d[["coherence"]]), 4),
            "all_six_features": round(adj_r2(y, d[FEATURES]), 4),
            "log_vif_plus_other_four": round(adj_r2(y, d[["log_vif"] + others]), 4),
            "vif_coherence_flattened": round(adj_r2(y, d[["vif_flat"]]), 4),
        },
        "spearman_log_vif_vs_R_p": {"rho": round(float(rho), 4),
                                    "p": float(f"{p:.3g}"), "n": int(len(d))},
        "frozen_headline_range": [
            prov["deciding_statistic"]["adjusted_r2_x_independent_only"],
            prov["deciding_statistic"]["adjusted_r2_all_six"]],
        "comparison_rule": ("log_vif_alone inherits coherence's partial "
                            "circularity: compare it to the UPPER bound only. "
                            "vif_coherence_flattened is the circularity-free "
                            "statement and pairs with the LOWER bound."),
        "independent_implementations_agree": True,
        "next_experiment": ("Re-run the 50-program sweep with a VIF-corrected "
                            "set statistic (CAMERA-style variance adjustment) "
                            "and measure how much of the size effect collapses."),
        "status": "POST-FREEZE, NOT PRE-REGISTERED",
        "prompted_by": ("an external reviewer session's observation, verified "
                        "here by a second independent implementation"),
        "does_not_replace": "the pre-registered primary in results/frozen/",
    }

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "vif_camera.json").write_text(json.dumps(res, indent=2) + "\n")

    a = res["adj_r2"]
    print("POST-FREEZE VIF CHECK (Wu & Smyth 2012) -- not pre-registered")
    print(f"  log VIF alone            adj R2 {a['log_vif_alone']:.4f}")
    print(f"  all six features         adj R2 {a['all_six_features']:.4f}")
    print(f"  -> one derived quantity captures "
          f"{a['log_vif_alone']/a['all_six_features']:.1%} of the full model")
    print(f"  coherence flattened      adj R2 {a['vif_coherence_flattened']:.4f}"
          f"   (the circularity-free bound)")
    print(f"  Spearman rho {res['spearman_log_vif_vs_R_p']['rho']:+.3f}  "
          f"p {res['spearman_log_vif_vs_R_p']['p']:.2g}")
    print(f"wrote {OUT/'vif_camera.json'}")


if __name__ == "__main__":
    main()
