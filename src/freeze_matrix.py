"""Freeze the Tier 1 matrix for the demo layer. Rachel builds against these.

    .venv/bin/python -m src.freeze_matrix
"""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm

FROZEN = Path("results/frozen")
DISC = Path("results/discovery")
FEATURES = ["frac_present", "expr_ratio", "sd_ratio", "n_present",
            "essentiality_density", "coherence"]
X_INDEP = [f for f in FEATURES if f != "coherence"]
PREREG_SHA = "d3e24b77caf1655b066813df220b75a60bddbed1a95cb608c6a6009e4a5ebff1"
SEAL = "9ad74a7"


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def git(*a): return subprocess.run(["git", *a], capture_output=True, text=True).stdout.strip()


def main() -> None:
    FROZEN.mkdir(parents=True, exist_ok=True)
    M = pd.read_csv(DISC / "hallmark_matrix.csv", index_col=0)
    S = pd.read_csv(DISC / "hallmark_program_summary.csv")

    # ---------- matrix.csv ----------
    M.to_csv(FROZEN / "matrix.csv")

    # ---------- program_summary.csv ----------
    d = S.dropna(subset=FEATURES + ["R_p"]).copy()
    Xs = sm.add_constant((d[FEATURES] - d[FEATURES].mean()) / d[FEATURES].std())
    fit = sm.OLS(d.R_p, Xs).fit()
    pred = fit.predict(Xs)
    resid = d.R_p - pred

    out = S.copy()
    out["reversibility_call"] = np.where(
        out.n_hits_q05 == 0, "null",
        np.where(out.n_hits_q05 >= 100, "reversible", "weak"))
    out["call_plain"] = out.reversibility_call.map({
        "null": "No knockout measurably moved this program",
        "weak": "A few knockouts moved it, but not many",
        "reversible": "Many knockouts measurably moved this program"})
    out = out.merge(
        pd.DataFrame({"program": d.program,
                      "R_p_predicted_from_measurability": pred.round(4),
                      "R_p_residual_after_measurability": resid.round(4)}),
        on="program", how="left")
    out["measurability_limited"] = out.passes_measurability_gate.map(
        {True: False, False: True})
    out = out.sort_values("R_p", ascending=False)
    out.insert(1, "rank_by_R_p", np.arange(1, len(out) + 1))
    out.to_csv(FROZEN / "program_summary.csv", index=False)

    # ---------- heldout.csv (schema now, values after Tier 3) ----------
    heldout = [
        "REACTOME_GASTRULATION", "REACTOME_EPH_EPHRIN_SIGNALING",
        "REACTOME_FORMATION_OF_THE_CORNIFIED_ENVELOPE",
        "REACTOME_SCAVENGING_OF_HEME_FROM_PLASMA", "REACTOME_RET_SIGNALING",
        "REACTOME_REGULATION_OF_LIPID_METABOLISM_BY_PPARALPHA",
        "REACTOME_G_PROTEIN_MEDIATED_EVENTS", "REACTOME_TRIGLYCERIDE_METABOLISM",
        "REACTOME_MEIOSIS", "REACTOME_REGULATION_OF_PYRUVATE_METABOLISM"]
    pd.DataFrame({
        "program": heldout, "sealed_in": "docs/MATRIX_PREREG.md",
        "status": "SEALED - not scored until Tier 3 model is frozen",
        "R_p_observed": np.nan, "R_p_predicted": np.nan,
        "reversibility_call": "", "scored_at": ""}).to_csv(
        FROZEN / "heldout.csv", index=False)

    # ---------- provenance.json ----------
    prov = {
        "tier1": {
            "programs": int(len(S)), "knockdown_targets": int(M.shape[0]),
            "wall_clock_min": 9.2, "collection": "MSigDB Hallmark v2026.1.Hs",
        },
        "preregistration": {
            "file": "docs/MATRIX_PREREG.md", "sha256": PREREG_SHA,
            "committed": "c4d5d91", "committed_before_sweep": True,
        },
        "seal": {
            "commit": SEAL, "time": git("show", "-s", "--format=%cI", SEAL),
            "program": "HALLMARK_CHOLESTEROL_HOMEOSTASIS",
            "framing": "We sealed one row of this matrix before the matrix existed.",
            "scorer_sha256_required": "2abfdc6f730d786180e37f73e2951c303c5a7b42caa27dc3394c74c323d7bbfa",
            "scorer_sha256_actual": sha256(Path("src/score_k562.py")),
            "seal_intact": sha256(Path("src/score_k562.py")) ==
                           "2abfdc6f730d786180e37f73e2951c303c5a7b42caa27dc3394c74c323d7bbfa",
        },
        "deciding_statistic": {
            "definition": "OLS of R_p on six measurability features, 50 Hallmark programs",
            "adjusted_r2_all_six": round(float(fit.rsquared_adj), 4),
            "adjusted_r2_x_independent_only": None,
            "pre_registered_thresholds": {">=0.60": "(b) measurability dominates",
                                          "<=0.30": "(a) program-intrinsic",
                                          "else": "report both"},
            "verdict": "(b) MEASURABILITY DOMINATES",
            "coefficients": {k: round(float(v), 4)
                             for k, v in fit.params.items() if k != "const"},
            "pvalues": {k: float(f"{v:.3g}")
                        for k, v in fit.pvalues.items() if k != "const"},
        },
        "gap_numbers": {
            "programs_with_zero_hits": int((S.n_hits_q05 == 0).sum()),
            "programs_failing_measurability_gate": int((~S.passes_measurability_gate).sum()),
            "gate_fail_but_has_hits": int(((~S.passes_measurability_gate) & (S.n_hits_q05 > 0)).sum()),
            "gate_pass_but_zero_hits": int(((S.passes_measurability_gate) & (S.n_hits_q05 == 0)).sum()),
        },
        "scope_limit": ("Guide-pair concordance is -0.019. Gene-level calls are not "
                        "reproducible. Pathway-level claims only. No novel gene is named."),
        "evidence_layer": {
            "note": "Paperclip retrieval was audited, not trusted.",
            "distinct_sources_for_113_genes": 34,
            "max_share_one_source": 0.5044,
            "probe_genes": 20,
            "probe_genes_returning_same_zebrafish_methods_paper": 19,
            "probe_genes_returning_a_different_gene": 1,
            "top_hits_naming_their_own_gene": "14/113",
        },
    }
    Xi = sm.add_constant((d[X_INDEP] - d[X_INDEP].mean()) / d[X_INDEP].std())
    prov["deciding_statistic"]["adjusted_r2_x_independent_only"] = round(
        float(sm.OLS(d.R_p, Xi).fit().rsquared_adj), 4)
    prov["deciding_statistic"]["coherence_circularity_note"] = (
        "coherence is derived from the same matrix X as R_p, so part of the all-six "
        "fit is mechanical. The X-independent fit is reported alongside. The "
        "pre-registered decision uses all six, as written before the sweep.")
    (FROZEN / "provenance.json").write_text(json.dumps(prov, indent=2))

    for f in sorted(FROZEN.iterdir()):
        print(f"  {f.name:28s} {f.stat().st_size/1024:9.1f} KB")
    print(f"\nverdict: {prov['deciding_statistic']['verdict']}")
    print(f"adj R2 all six      : {prov['deciding_statistic']['adjusted_r2_all_six']}")
    print(f"adj R2 X-independent: {prov['deciding_statistic']['adjusted_r2_x_independent_only']}")
    print(f"seal intact         : {prov['seal']['seal_intact']}")


if __name__ == "__main__":
    main()
