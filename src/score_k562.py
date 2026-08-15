"""Pipeline step 2 — score all K562 knockdowns for opposition to a program.

Primary statistic: rank-based nonparametric (Mann-Whitney U of program-gene
effects vs all other genes, within each perturbation). Cosine similarity to the
program vector reported alongside as a baseline. Both reported; neither is
optimised alone.

Rationale (docs/WINNING_PATTERNS.md sections 7-8): the Virtual Cell Challenge PDS
leaderboard was topped on Wilcoxon + pseudobulk + distance calibration, and the
overall winner was ranked by average rank across seven metrics.

Usage:  .venv/bin/python score_k562.py <SET_NAME> <out.csv>
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import h5py
import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu

K562 = Path("data/raw/K562_gwps_normalized_bulk_01.h5ad")
GMT_DIR = Path("data/genesets")


def load_sets() -> dict[str, list[str]]:
    s: dict[str, list[str]] = {}
    for g in GMT_DIR.glob("*.symbols.gmt"):
        for line in g.read_text().splitlines():
            p = line.split("\t")
            if len(p) > 2:
                s[p[0]] = p[2:]
    return s


def load_k562():
    with h5py.File(K562, "r") as f:
        cats = [c.decode() if isinstance(c, bytes) else c
                for c in f["var/__categories/gene_name"][:]]
        codes = f["var/gene_name"][:]
        symbols = np.array([cats[c] if 0 <= c < len(cats) else "" for c in codes])
        pert = [x.decode() if isinstance(x, bytes) else x
                for x in f["obs/gene_transcript"][:]]
        X = f["X"][:].astype(np.float64)
    X[~np.isfinite(X)] = np.nan
    targets = []
    for s in pert:
        m = re.match(r"^\d+_(.+?)_(?:P1P2|P1|P2|ENST[\d.,]+)_", s)
        targets.append(m.group(1) if m else None)
    return X, symbols, np.array(pert), np.array(targets, dtype=object)


def score(X, symbols, program: list[str]):
    """Return per-perturbation opposition scores.

    Sign convention: the program is UP in disease, so OPPOSING it means the
    knockdown pushes program genes DOWN relative to the rest of the
    transcriptome. A more negative mean program effect => stronger opposition.
    Reported scores are oriented so that HIGHER = STRONGER OPPOSITION.
    """
    idx = np.where(np.isin(symbols, program))[0]
    bg = np.setdiff1d(np.arange(len(symbols)), idx)
    n_pert = X.shape[0]

    u_z = np.full(n_pert, np.nan)      # primary: rank-based
    cos = np.full(n_pert, np.nan)      # baseline: cosine
    delta = np.full(n_pert, np.nan)    # effect size: mean program - mean background

    # program direction vector: +1 on each program gene, 0 elsewhere
    v = np.zeros(len(symbols))
    v[idx] = 1.0
    v_norm = np.linalg.norm(v)

    for i in range(n_pert):
        row = X[i]
        a, b = row[idx], row[bg]
        a, b = a[np.isfinite(a)], b[np.isfinite(b)]
        if len(a) < 10 or len(b) < 100:
            continue
        # two-sided U, converted to a signed z so direction is preserved
        u = mannwhitneyu(a, b, alternative="two-sided")
        n1, n2 = len(a), len(b)
        mu = n1 * n2 / 2.0
        sd = np.sqrt(n1 * n2 * (n1 + n2 + 1) / 12.0)
        z = (u.statistic - mu) / sd
        u_z[i] = -z                       # flip: higher = program pushed DOWN
        delta[i] = -(np.mean(a) - np.mean(b))
        r = np.nan_to_num(row, nan=0.0)
        rn = np.linalg.norm(r)
        cos[i] = -(float(r @ v) / (rn * v_norm)) if rn > 0 else np.nan

    return u_z, cos, delta, len(idx)


def main() -> None:
    set_name = sys.argv[1]
    out = Path(sys.argv[2])
    sets = load_sets()
    if set_name not in sets:
        raise SystemExit(f"{set_name} not in GMTs")
    program = sets[set_name]

    X, symbols, pert, targets = load_k562()
    u_z, cos, delta, n_present = score(X, symbols, program)

    df = pd.DataFrame({
        "perturbation": pert, "target": targets,
        "u_z": u_z, "cosine": cos, "delta": delta,
    })
    df["rank_u_z"] = df.u_z.rank(ascending=False, method="min")
    df["rank_cosine"] = df.cosine.rank(ascending=False, method="min")
    df["rank_delta"] = df.delta.rank(ascending=False, method="min")
    # average-rank composite, per the Virtual Cell Challenge winner's scheme
    df["avg_rank"] = df[["rank_u_z", "rank_cosine", "rank_delta"]].mean(axis=1)
    df = df.sort_values("avg_rank")

    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False)

    sp = df.u_z.corr(df.cosine, method="spearman")
    print(f"set                : {set_name}")
    print(f"program genes      : {len(program)} declared, {n_present} measured in K562")
    print(f"perturbations      : {len(df)} rows, {df.target.nunique()} unique targets")
    print(f"scored (non-NaN)   : {df.u_z.notna().sum()}")
    print(f"Spearman u_z~cosine: {sp:.3f}   <- metric agreement, not a headline")
    print(f"\nwrote {out}\n")
    print("TOP 15 by average rank across the three metrics:")
    print(df.head(15)[["target", "u_z", "cosine", "delta", "avg_rank"]]
          .to_string(index=False, float_format=lambda x: f"{x:.3f}"))


if __name__ == "__main__":
    main()
