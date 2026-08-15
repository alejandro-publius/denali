"""Tier 2 — open and score the sealed ten. RUN ONLY AFTER predictor.json is committed.

Predictions come from the FROZEN predictor (results/frozen/predictor.json,
sha256 610f2a75...). Nothing is refit here. Whatever the numbers say is reported.

    .venv/bin/python -m src.score_heldout
"""
from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path

import h5py
import numpy as np
import pandas as pd
from scipy.stats import norm, spearmanr
from statsmodels.stats.multitest import multipletests

from src.score_k562 import load_k562, score

FROZEN = Path("results/frozen")
REACTOME = "data/genesets/c2.cp.reactome.v2026.1.Hs.symbols.gmt"
EXPECTED_PRED_SHA = "610f2a75dd11f9e28471aa552c587d2b500f81d4fbc5d5bc0dd96eb3acc819b6"


def features(program, symbols, expr, sd, X, ess):
    idx = np.where(np.isin(symbols, program))[0]
    bg = np.setdiff1d(np.arange(len(symbols)), idx)
    n = len(idx)
    if n < 2:
        # coherence is undefined for <2 measured members. Set NaN here; the caller
        # substitutes the TRAINING MEAN so the feature contributes z=0 (neutral)
        # and flags the row. Disclosed; the frozen predictor is not modified.
        coh = np.nan
    else:
        sub = np.nan_to_num(X[:, idx], nan=0.0)
        c = np.corrcoef(sub, rowvar=False)
        iu = np.triu_indices_from(c, k=1)
        coh = float(np.nanmean(c[iu]))
    if n == 0:
        return {"n_declared": len(program), "n_present": 0, "frac_present": 0.0,
                "expr_ratio": np.nan, "sd_ratio": np.nan,
                "essentiality_density": np.nan, "coherence": np.nan}
    return {
        "n_declared": len(program), "n_present": n,
        "frac_present": n / len(program),
        "expr_ratio": float(np.nanmedian(expr[idx]) / np.nanmedian(expr[bg])),
        "sd_ratio": float(np.nanmedian(sd[idx]) / np.nanmedian(sd[bg])),
        "essentiality_density": float(np.nanmean(ess.reindex(symbols[idx]).values < -0.5)),
        "coherence": coh,
    }


def main() -> None:
    P = json.loads((FROZEN / "predictor.json").read_text())
    actual = hashlib.sha256((FROZEN / "predictor.json").read_bytes()).hexdigest()
    assert actual == EXPECTED_PRED_SHA, f"predictor changed! {actual}"
    print(f"frozen predictor verified: {actual[:16]}...")

    F = P["features"]
    mu = pd.Series(P["standardisation"]["mean"])
    sdv = pd.Series(P["standardisation"]["std"])
    coef = P["coefficients"]
    thr_rp = P["binary_rule"]["reversible_iff_predicted_R_p_at_least"]
    min_hits = P["binary_rule"]["reversible_iff_hits_at_least"]
    G = P["gate_criteria"]

    heldout = list(pd.read_csv(FROZEN / "heldout.csv").program)
    sets = {}
    for line in open(REACTOME):
        p = line.rstrip("\n").split("\t")
        if len(p) > 2:
            sets[p[0]] = p[2:]

    X, symbols, pert, targets = load_k562()
    with h5py.File("data/raw/K562_gwps_normalized_bulk_01.h5ad", "r") as f:
        expr = f["var/mean"][:].astype(float)
    sd_all = np.nanstd(X, axis=0)
    dm = pd.read_csv("data/raw/CRISPRGeneEffect.csv", index_col=0)
    dm.columns = [c.split(" (")[0] for c in dm.columns]
    ess = dm.mean(axis=0)

    rows = []
    t0 = time.time()
    for i, name in enumerate(heldout, 1):
        prog = sets[name]
        f = features(prog, symbols, expr, sd_all, X, ess)
        # undefined features fall back to the TRAINING MEAN -> z = 0, neutral.
        imputed = [k for k in F if not np.isfinite(f[k])]
        for k in imputed:
            f[k] = float(mu[k])
        z = {k: (f[k] - mu[k]) / sdv[k] for k in F}
        pred = coef["const"] + sum(coef[k] * z[k] for k in F)

        u_z, cos, delta, npres = score(X, symbols, prog)      # <-- the seal opens here
        p = 2 * norm.sf(np.abs(u_z))
        ok = np.isfinite(p)
        q = np.full_like(p, np.nan)
        if ok.sum():
            q[ok] = multipletests(p[ok], method="fdr_bh")[1]
        # ok.sum()==0 means the program had too few measured members to score at
        # all -> 0 hits, and the row is flagged unscoreable rather than dropped.
        hits = int(np.nansum(q < 0.05))
        unscoreable = bool(ok.sum() == 0)
        obs = float(np.log10(1 + hits))
        gate = bool(f["frac_present"] >= G["min_frac_present"]
                    and f["n_present"] >= G["min_n_present"]
                    and f["expr_ratio"] >= G["min_expr_ratio"]
                    and f["sd_ratio"] >= G["min_sd_ratio"])
        rows.append({"program": name, **f, "R_p_predicted": round(pred, 4),
                     "n_hits_q05": hits, "R_p_observed": round(obs, 4),
                     "predicted_reversible": bool(pred >= thr_rp),
                     "observed_reversible": bool(hits >= min_hits),
                     "passes_gate": gate,
                     "residual": round(obs - pred, 4),
                     "imputed_features": ";".join(imputed),
                     "unscoreable": unscoreable})
        print(f"  [{i:2d}/10] {name[:46]:48s} pred={pred:5.2f} obs={obs:5.2f} "
              f"hits={hits:5d} gate={'Y' if gate else 'N'}")

    d = pd.DataFrame(rows)
    n_gate = int(d.passes_gate.sum())

    rho, pval = spearmanr(d.R_p_predicted, d.R_p_observed)
    rng = np.random.default_rng(20260815)
    boots = []
    for _ in range(1000):
        s = rng.integers(0, len(d), len(d))
        if len(set(d.R_p_observed.values[s])) > 1:
            boots.append(spearmanr(d.R_p_predicted.values[s], d.R_p_observed.values[s])[0])
    lo, hi = np.nanpercentile(boots, [2.5, 97.5])

    tp = int(((d.predicted_reversible) & (d.observed_reversible)).sum())
    tn = int(((~d.predicted_reversible) & (~d.observed_reversible)).sum())
    fp = int(((d.predicted_reversible) & (~d.observed_reversible)).sum())
    fn = int(((~d.predicted_reversible) & (d.observed_reversible)).sum())
    sens = tp / (tp + fn) if (tp + fn) else np.nan
    spec = tn / (tn + fp) if (tn + fp) else np.nan
    bal = np.nanmean([sens, spec])

    def v1(r):
        if r < 0: return "FAILURE, INVERTED"
        if r < 0.30: return "FAILURE"
        if r < 0.60: return "PARTIAL"
        return "SUCCESS"

    def v2(b):
        if np.isnan(b): return "UNDEFINED (one class absent)"
        if b < 0.55: return "FAILURE"
        if b < 0.75: return "PARTIAL"
        return "SUCCESS"

    underpowered = n_gate < 8
    res = {
        "predictor_sha256": actual,
        "n_heldout": len(d),
        "n_passing_gate": n_gate,
        "underpowered_and_inconclusive": underpowered,
        "axis1_spearman_rho": round(float(rho), 4),
        "axis1_p": float(f"{pval:.4g}"),
        "axis1_bootstrap_95ci": [round(float(lo), 4), round(float(hi), 4)],
        "axis1_verdict": v1(rho),
        "axis2_confusion": {"tp": tp, "tn": tn, "fp": fp, "fn": fn},
        "axis2_sensitivity": None if np.isnan(sens) else round(float(sens), 4),
        "axis2_specificity": None if np.isnan(spec) else round(float(spec), 4),
        "axis2_balanced_accuracy": None if np.isnan(bal) else round(float(bal), 4),
        "axis2_verdict": v2(bal),
        "refit_after_seeing_results": False,
        "wall_clock_min": round((time.time() - t0) / 60, 2),
    }
    d.to_csv(FROZEN / "heldout.csv", index=False)
    (FROZEN / "heldout_evaluation.json").write_text(json.dumps(res, indent=2))

    print("\n" + "=" * 66)
    print(f"gate-passing        : {n_gate}/10"
          + ("   -> UNDERPOWERED AND INCONCLUSIVE" if underpowered else ""))
    print(f"AXIS 1 Spearman rho : {rho:+.4f}  95% CI [{lo:+.3f}, {hi:+.3f}]  p={pval:.3g}")
    print(f"AXIS 1 VERDICT      : {res['axis1_verdict']}")
    print(f"AXIS 2 balanced acc : {bal if not np.isnan(bal) else float('nan'):.4f}"
          f"  (tp={tp} tn={tn} fp={fp} fn={fn})")
    print(f"AXIS 2 VERDICT      : {res['axis2_verdict']}")
    print("=" * 66)
    print("Reported as measured. No refit.")


if __name__ == "__main__":
    main()
