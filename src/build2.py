"""Build II — RPE1 arm + DepMap essentiality filter + three controls.

Framing settled in Section 3: two-tier output with an ESSENTIALITY-MATCHED NULL
(#7 + #2). RPE1 is the cross-cell-type generalisation check with an honest
denominator, NOT the replication arm. Guide-pair concordance is a third control.

Usage: .venv/bin/python build2.py <SET_NAME> <k562_scores.csv> <out_prefix>
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import h5py
import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu

GMT_DIR = Path("data/genesets")
RPE1 = Path("data/raw/rpe1_normalized_bulk_01.h5ad")
DEPMAP = Path("data/raw/CRISPRGeneEffect.csv")
SEED = 20260815          # pre-committed in docs/HELDOUT_PROGRAM.md
N_NONSENSE = 41          # pre-committed
ESSENTIAL_CUT = -0.5     # DepMap Chronos convention: < -0.5 = depleting


def load_sets():
    s = {}
    for g in GMT_DIR.glob("*.symbols.gmt"):
        for line in g.read_text().splitlines():
            p = line.split("\t")
            if len(p) > 2:
                s[p[0]] = p[2:]
    return s


def load_h5(path):
    with h5py.File(path, "r") as f:
        cats = [c.decode() if isinstance(c, bytes) else c
                for c in f["var/__categories/gene_name"][:]]
        codes = f["var/gene_name"][:]
        symbols = np.array([cats[c] if 0 <= c < len(cats) else "" for c in codes])
        pert = [x.decode() if isinstance(x, bytes) else x
                for x in f["obs/gene_transcript"][:]]
        X = f["X"][:].astype(np.float64)
    X[~np.isfinite(X)] = np.nan
    tg = []
    for s in pert:
        m = re.match(r"^\d+_(.+?)_(?:P1P2|P1|P2|ENST[\d.,]+)_", s)
        tg.append(m.group(1) if m else None)
    return X, symbols, np.array(pert), np.array(tg, dtype=object)


def score(X, symbols, program):
    idx = np.where(np.isin(symbols, program))[0]
    bg = np.setdiff1d(np.arange(len(symbols)), idx)
    out = np.full(X.shape[0], np.nan)
    for i in range(X.shape[0]):
        a, b = X[i][idx], X[i][bg]
        a, b = a[np.isfinite(a)], b[np.isfinite(b)]
        if len(a) < 10 or len(b) < 100:
            continue
        u = mannwhitneyu(a, b, alternative="two-sided")
        n1, n2 = len(a), len(b)
        mu = n1 * n2 / 2.0
        sd = np.sqrt(n1 * n2 * (n1 + n2 + 1) / 12.0)
        out[i] = -((u.statistic - mu) / sd)
    return out, len(idx)


def main():
    set_name, k_path, prefix = sys.argv[1], sys.argv[2], sys.argv[3]
    sets = load_sets()
    program = sets[set_name]
    k = pd.read_csv(k_path)
    kbest = k.loc[k.groupby("target").u_z.idxmax()].set_index("target")

    # ---------- RPE1 arm ----------
    Xr, symr, pertr, tgr = load_h5(RPE1)
    rz, n_prog_rpe1 = score(Xr, symr, program)
    rdf = pd.DataFrame({"target": tgr, "rpe1_u_z": rz}).dropna(subset=["target"])
    rdf = rdf.loc[rdf.groupby("target").rpe1_u_z.idxmax()].set_index("target")
    rdf["rpe1_rank"] = rdf.rpe1_u_z.rank(ascending=False, method="min")

    n_k = kbest.index.nunique()
    n_r = rdf.index.nunique()
    n_ov = len(set(kbest.index) & set(rdf.index))
    print(f"RPE1 program genes measured : {n_prog_rpe1}")
    print(f"RPE1 DENOMINATOR            : {n_ov}/{n_k} = {100*n_ov/n_k:.1f}% of K562 targets covered")

    # ---------- DepMap ----------
    dm = pd.read_csv(DEPMAP, index_col=0)
    dm.columns = [c.split(" (")[0] for c in dm.columns]
    ess = dm.mean(axis=0)                      # mean Chronos across ~1150 lines
    ess_n = dm.notna().sum(axis=0)
    print(f"DepMap genes                : {len(ess)}   lines: {dm.shape[0]}")

    res = kbest[["u_z", "cosine", "delta", "avg_rank"]].copy()
    res = res.join(rdf[["rpe1_u_z", "rpe1_rank"]], how="left")
    res["rpe1_covered"] = res.rpe1_u_z.notna()
    res["depmap_chronos"] = ess.reindex(res.index)
    res["depmap_n_lines"] = ess_n.reindex(res.index)
    res["essential"] = res.depmap_chronos < ESSENTIAL_CUT
    res["depmap_covered"] = res.depmap_chronos.notna()
    res = res.sort_values("avg_rank")

    # ---------- TIERS (Section 3 framing) ----------
    def tier(r):
        if not r.depmap_covered:
            return "T3_no_fitness_data"
        if r.essential:
            return "T2_reversal_confounded_by_essentiality"
        return "T1_reversal_not_explained_by_fitness"
    res["tier"] = res.apply(tier, axis=1)
    res.to_csv(f"{prefix}_ranked.csv")
    print("\n=== TIER COUNTS ===")
    print(res.tier.value_counts().to_string())

    # ---------- CONTROL 2: essentiality-matched null ----------
    top = res.head(50)
    frac_ess_top = float(top.essential.mean())
    frac_ess_all = float(res.essential.mean())
    print(f"\n=== ESSENTIALITY-MATCHED NULL ===")
    print(f"fraction essential in TOP 50 : {frac_ess_top:.3f}")
    print(f"fraction essential overall   : {frac_ess_all:.3f}")
    print(f"enrichment                   : {frac_ess_top/frac_ess_all:.2f}x")
    rng = np.random.default_rng(SEED)
    draws = [res.essential.sample(50, random_state=int(rng.integers(1e9))).mean()
             for _ in range(1000)]
    p_emp = float(np.mean([d >= frac_ess_top for d in draws]))
    print(f"empirical p (1000 draws)     : {p_emp:.4f}")

    # RPE1 coverage inside vs outside essential
    cov_ess = res[res.essential].rpe1_covered.mean()
    cov_non = res[~res.essential].rpe1_covered.mean()
    print(f"RPE1 coverage | essential    : {cov_ess:.3f}")
    print(f"RPE1 coverage | NOT essential: {cov_non:.3f}   <- the collision, quantified")

    # ---------- CONTROL 1: held-out known UPR regulators ----------
    known = ["ERN1", "ATF6", "EIF2AK3", "XBP1", "ATF4", "DDIT3", "HSPA5", "EDEM1", "SEL1L", "HERPUD1"]
    print("\n=== CONTROL 1: recovery rank of known UPR regulators ===")
    tot = len(res)
    for g in known:
        if g in res.index:
            r = res.loc[g]
            print(f"  {g:9s} rank {int(r.avg_rank):>6d}/{tot}  u_z {r.u_z:+.2f}  "
                  f"pct {100*r.avg_rank/tot:5.1f}%  ess={bool(r.essential)}")
        else:
            print(f"  {g:9s} NOT PERTURBED in screen")

    # ---------- CONTROL 3: nonsense program ----------
    rng2 = np.random.default_rng(SEED)
    Xk, symk, pertk, tgk = load_h5(Path("data/raw/K562_gwps_normalized_bulk_01.h5ad"))
    nonsense = list(rng2.choice(symk[symk != ""], N_NONSENSE, replace=False))
    nz, _ = score(Xk, symk, nonsense)
    ndf = pd.DataFrame({"target": tgk, "u_z": nz}).dropna(subset=["target"])
    from scipy.stats import norm
    from statsmodels.stats.multitest import multipletests
    p = 2 * norm.sf(np.abs(ndf.u_z.values))
    q = multipletests(p, method="fdr_bh")[1]
    print(f"\n=== CONTROL 3: nonsense program ({N_NONSENSE} random genes, seed {SEED}) ===")
    print(f"  genes: {', '.join(sorted(nonsense)[:8])} ...")
    print(f"  perturbations surviving q<0.05 : {int((q<0.05).sum())}")
    print(f"  max |u_z|                      : {np.nanmax(np.abs(ndf.u_z)):.2f}")

    # real program, same test, for comparison
    pk = 2 * norm.sf(np.abs(k.u_z.values))
    qk = multipletests(pk, method="fdr_bh")[1]
    print(f"  REAL program surviving q<0.05  : {int((qk<0.05).sum())}   <- comparison")

    # ---------- CONTROL 4: guide-pair concordance ----------
    gp = k.dropna(subset=["target"]).copy()
    gp["suffix"] = [re.search(r"_(P1P2|P1|P2)_", s).group(1)
                    if re.search(r"_(P1P2|P1|P2)_", s) else None for s in gp.perturbation]
    pair = gp[gp.suffix.isin(["P1", "P2"])].pivot_table(index="target", columns="suffix", values="u_z")
    pair = pair.dropna()
    if len(pair) > 10:
        rho = pair["P1"].corr(pair["P2"], method="spearman")
        print(f"\n=== CONTROL 4: guide-pair concordance ({len(pair)} genes with separate P1/P2) ===")
        print(f"  Spearman P1 vs P2 : {rho:.3f}")
    print(f"\nwrote {prefix}_ranked.csv")


if __name__ == "__main__":
    main()
