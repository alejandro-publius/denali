"""Tier 1 — 50 MSigDB Hallmark programs x 9,823 knockdowns, measurability-gated.

Calls the BYTE-IDENTICAL committed scorer from src/score_k562.py
(sha256 2abfdc6f730d786180e37f73e2951c303c5a7b42caa27dc3394c74c323d7bbfa).
If that statistic changes, program B's seal at 63596b5 is void -- see
docs/MATRIX_PREREG.md section 7.

Pre-registered in docs/MATRIX_PREREG.md, sha256 d3e24b77...

    .venv/bin/python -m src.sweep
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import norm
from statsmodels.stats.multitest import multipletests

from src.score_k562 import load_k562, load_sets, score

GMT = "data/genesets/h.all.v2026.1.Hs.symbols.gmt"
OUT_MATRIX = Path("results/discovery/hallmark_matrix.csv")
OUT_SUMMARY = Path("results/discovery/hallmark_program_summary.csv")
HELDOUT_B = "HALLMARK_CHOLESTEROL_HOMEOSTASIS"
PROGRAM_A = "HALLMARK_UNFOLDED_PROTEIN_RESPONSE"

# Gate C1 thresholds, unchanged from the committed gate
MIN_FRAC, MIN_N, ALPHA = 0.50, 25, 0.05


def hallmark() -> dict[str, list[str]]:
    s = {}
    for line in open(GMT):
        p = line.rstrip("\n").split("\t")
        if len(p) > 2:
            s[p[0]] = p[2:]
    return s


def features(program, symbols, expr, sd, X, ess) -> dict:
    """M1-M6, all computable WITHOUT scoring. Pre-registered."""
    idx = np.where(np.isin(symbols, program))[0]
    bg = np.setdiff1d(np.arange(len(symbols)), idx)
    n_present = len(idx)
    out = {
        "n_declared": len(program),
        "n_present": n_present,
        "frac_present": round(n_present / len(program), 4),
    }
    if n_present < 3:
        return {**out, "expr_ratio": np.nan, "sd_ratio": np.nan,
                "essentiality_density": np.nan, "coherence": np.nan}
    out["expr_ratio"] = round(float(np.nanmedian(expr[idx]) / np.nanmedian(expr[bg])), 4)
    out["sd_ratio"] = round(float(np.nanmedian(sd[idx]) / np.nanmedian(sd[bg])), 4)
    e = ess.reindex(symbols[idx]).values
    out["essentiality_density"] = round(float(np.nanmean(e < -0.5)), 4)
    # mean pairwise correlation among member genes across perturbations
    sub = X[:, idx]
    sub = np.nan_to_num(sub, nan=0.0)
    if n_present > 1:
        c = np.corrcoef(sub, rowvar=False)
        iu = np.triu_indices_from(c, k=1)
        out["coherence"] = round(float(np.nanmean(c[iu])), 4)
    else:
        out["coherence"] = np.nan
    return out


def main() -> None:
    t0 = time.time()
    X, symbols, pert, targets = load_k562()
    expr_all = None
    import h5py
    with h5py.File("data/raw/K562_gwps_normalized_bulk_01.h5ad", "r") as f:
        expr_all = f["var/mean"][:].astype(float)
    sd_all = np.nanstd(X, axis=0)

    dm = pd.read_csv("data/raw/CRISPRGeneEffect.csv", index_col=0)
    dm.columns = [c.split(" (")[0] for c in dm.columns]
    ess = dm.mean(axis=0)

    sets = hallmark()
    print(f"loaded in {time.time()-t0:.1f}s | {len(sets)} Hallmark programs | X {X.shape}")

    mat, rows = {}, []
    for i, (name, program) in enumerate(sorted(sets.items()), 1):
        t = time.time()
        u_z, cos, delta, n_present = score(X, symbols, program)
        p = 2 * norm.sf(np.abs(u_z))
        ok = np.isfinite(p)
        q = np.full_like(p, np.nan)
        if ok.sum():
            q[ok] = multipletests(p[ok], method="fdr_bh")[1]
        n_hits = int(np.nansum(q < ALPHA))
        R_p = float(np.log10(1 + n_hits))

        f = features(program, symbols, expr_all, sd_all, X, ess)
        gate = bool(f["frac_present"] >= MIN_FRAC and f["n_present"] >= MIN_N
                    and (f["expr_ratio"] or 0) >= 1.0 and (f["sd_ratio"] or 0) >= 1.0)

        mat[name] = pd.Series(u_z, index=pert).groupby(
            pd.Series(targets, index=pert)).max()

        rows.append({"program": name, **f, "n_hits_q05": n_hits, "R_p": round(R_p, 4),
                     "passes_measurability_gate": gate,
                     "is_held_out_program": name == HELDOUT_B,
                     "is_program_A": name == PROGRAM_A})
        print(f"  [{i:2d}/50] {name[:48]:50s} hits={n_hits:5d} R_p={R_p:.3f} "
              f"gate={'Y' if gate else 'N'} ({time.time()-t:.1f}s)")

    M = pd.DataFrame(mat)
    M.index.name = "target_gene"
    M.to_csv(OUT_MATRIX)
    S = pd.DataFrame(rows).sort_values("R_p", ascending=False)
    S.to_csv(OUT_SUMMARY, index=False)

    el = time.time() - t0
    print(f"\nWALL-CLOCK: {el/60:.1f} min")
    print(f"matrix  {OUT_MATRIX}  {M.shape}")
    print(f"summary {OUT_SUMMARY}  {S.shape}")
    print(f"\ngate passed : {int(S.passes_measurability_gate.sum())}/50")
    print(f"R_p > 0     : {int((S.R_p>0).sum())}/50")
    print(f"zero hits   : {int((S.n_hits_q05==0).sum())}/50")
    b = S[S.is_held_out_program].iloc[0]
    print(f"\nheld-out program B rank by R_p: "
          f"{int(S.reset_index(drop=True).index[S.reset_index(drop=True).program==HELDOUT_B][0])+1}/50 "
          f"(R_p={b.R_p}, hits={b.n_hits_q05}, gate={b.passes_measurability_gate})")


if __name__ == "__main__":
    main()
