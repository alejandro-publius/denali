"""Four figures, from our own data only. No protein renders, no borrowed outputs.

A structure on screen would imply a gene-level claim our -0.019 concordance
forbids. Everything here is measured in this repo.

    .venv/bin/python -m src.figures_matrix
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import TwoSlopeNorm

OUT = Path("results/figures")
FROZEN = Path("results/frozen")
PROBE = Path("/private/tmp/claude-501/-Users-alexvintera/"
             "7dc2189b-1701-4701-beee-bcd03999de85/scratchpad/probe_paperclip.json")
DPI = 150
SEALED = "HALLMARK_CHOLESTEROL_HOMEOSTASIS"
plt.rcParams.update({"font.size": 9, "axes.spines.top": False,
                     "axes.spines.right": False, "figure.dpi": DPI})


def fig1(S, M):
    order = S.sort_values("n_hits_q05", ascending=False).program.tolist()
    A = M[order].values
    v = np.nanpercentile(np.abs(A), 99)
    fig, ax = plt.subplots(figsize=(11, 6.5))
    im = ax.imshow(A, aspect="auto", cmap="RdBu_r",
                   norm=TwoSlopeNorm(vmin=-v, vcenter=0, vmax=v),
                   interpolation="nearest")
    ax.set_xlabel("50 MSigDB Hallmark programs  (ordered by number of hits, most → fewest)")
    ax.set_ylabel("9,837 CRISPRi knockdowns")
    ax.set_yticks([])
    ax.set_xticks(range(0, 50, 5))
    ax.set_xticklabels([str(i) for i in range(0, 50, 5)])
    si = order.index(SEALED)
    ax.axvline(si, color="k", lw=1.4, ls="--")
    ax.text(si + 0.7, A.shape[0] * 0.045, f"sealed program\n(rank {si+1}/50)",
            fontsize=8, va="top")
    cb = fig.colorbar(im, ax=ax, pad=0.015, fraction=0.03)
    cb.set_label("program pushed DOWN  ←    reversal score    →  pushed UP", fontsize=8)
    ax.set_title("The reversal matrix: every knockdown scored against every program",
                 fontsize=11, loc="left")
    fig.tight_layout(); fig.savefig(OUT / "fig1_matrix.png"); plt.close(fig)


def fig2(S):
    fig, ax = plt.subplots(figsize=(8, 5.5))
    x = S.passes_measurability_gate.map({True: 1, False: 0}) + \
        np.random.default_rng(0).normal(0, 0.055, len(S))
    y = S.n_hits_q05 + 1
    ax.axhspan(1, 1.6, xmin=0, xmax=0.5, color="#d9d9d9", alpha=0.35)
    ax.axhspan(1.6, y.max() * 2, xmin=0, xmax=0.5, color="#f4a582", alpha=0.30)
    ax.text(-0.42, y.max() * 0.9, "FAILS the gate,\nproduces hits anyway\n"
            f"{int(((~S.passes_measurability_gate)&(S.n_hits_q05>0)).sum())} of 50",
            fontsize=9, color="#b2182b", weight="bold", va="top")
    ax.scatter(x, y, s=34, c=np.where(S.n_hits_q05 > 0, "#2166ac", "#999999"),
               alpha=0.85, edgecolor="white", lw=0.6, zorder=3)
    srow = S[S.program == SEALED].iloc[0]
    sx = 1 if srow.passes_measurability_gate else 0
    ax.scatter([sx], [srow.n_hits_q05 + 1], s=190, facecolor="none",
               edgecolor="#b2182b", lw=2.2, zorder=5)
    ax.annotate(f"SEALED program\nfails the gate (expr_ratio {srow.expr_ratio:.2f})\n"
                f"rank {int(srow.rank_by_R_p)}/50, {int(srow.n_hits_q05)} hits",
                xy=(sx, srow.n_hits_q05 + 1), xytext=(0.28, 1400),
                fontsize=8.5, color="#b2182b",
                arrowprops=dict(arrowstyle="->", color="#b2182b", lw=1.2))
    ax.set_yscale("log"); ax.set_xlim(-0.5, 1.5); ax.set_xticks([0, 1])
    ax.set_xticklabels(["FAILS measurability gate", "PASSES measurability gate"])
    ax.set_ylabel("knockdowns that moved the program  (+1, log scale)")
    ax.set_title("The filter anyone would build is wrong 20 times out of 50",
                 fontsize=11, loc="left")
    fig.tight_layout(); fig.savefig(OUT / "fig2_gate_failure.png"); plt.close(fig)


def fig3(S, prov):
    import statsmodels.api as sm
    d = S.dropna(subset=["n_present", "R_p"])
    fig, ax = plt.subplots(figsize=(8, 5.5))
    ax.scatter(d.n_present, d.R_p, s=36, c="#2166ac", alpha=0.8,
               edgecolor="white", lw=0.6)
    X = sm.add_constant(d.n_present)
    m = sm.OLS(d.R_p, X).fit()
    xs = np.linspace(d.n_present.min(), d.n_present.max(), 100)
    ax.plot(xs, m.params.iloc[0] + m.params.iloc[1] * xs, color="#b2182b", lw=2)
    r_lo = prov["deciding_statistic"]["adjusted_r2_x_independent_only"]
    r_hi = prov["deciding_statistic"]["adjusted_r2_all_six"]
    ax.text(0.03, 0.96,
            f"program size alone:  R² = {m.rsquared:.2f}\n"
            f"all measurability features:  adj R² = {r_lo:.2f} – {r_hi:.2f}\n"
            f"(range because one feature is partly circular)",
            transform=ax.transAxes, va="top", fontsize=9.5,
            bbox=dict(boxstyle="round,pad=0.5", fc="#fff3e0", ec="#e0a458"))
    ax.set_xlabel("program size  (members actually measured)")
    ax.set_ylabel("R_p = log10(1 + hits)")
    ax.set_title("Bigger programs return more hits regardless of what they do",
                 fontsize=11, loc="left")
    fig.tight_layout(); fig.savefig(OUT / "fig3_measurability.png"); plt.close(fig)


def fig4():
    rows = json.loads(PROBE.read_text())
    src = {}
    for r in rows:
        for c in r["claims"]:
            src.setdefault(c, set()).add(r["gene"])
    shared = sorted(src.items(), key=lambda kv: -len(kv[1]))
    top_text, top_genes = shared[0]
    genes = [r["gene"] for r in rows]

    fig, ax = plt.subplots(figsize=(9.5, 7))
    gy = {g: i for i, g in enumerate(genes)}
    keep = [(t, gs) for t, gs in shared[:6]]
    sy = np.linspace(0, len(genes) - 1, len(keep))
    for j, (t, gs) in enumerate(keep):
        col = "#b2182b" if t == top_text else "#bbbbbb"
        lw = 1.5 if t == top_text else 0.6
        for g in gs:
            ax.plot([0, 1], [gy[g], sy[j]], color=col, lw=lw,
                    alpha=0.85 if t == top_text else 0.45, zorder=1)
    ax.scatter([0] * len(genes), list(gy.values()), s=42, c="#2166ac", zorder=3)
    for g, y in gy.items():
        ax.text(-0.035, y, g, ha="right", va="center", fontsize=8)
    ax.scatter([1] * len(keep), sy, s=70, c=["#b2182b" if t == top_text else "#888888"
                                             for t, _ in keep], zorder=3)
    for j, (t, gs) in enumerate(keep):
        lab = t[:52] + ("…" if len(t) > 52 else "")
        ax.text(1.04, sy[j], f"{lab}\n({len(gs)} genes)", va="center", fontsize=7.5,
                color="#b2182b" if t == top_text else "#444444",
                weight="bold" if t == top_text else "normal")
    ax.set_xlim(-0.35, 2.05); ax.set_ylim(-1, len(genes)); ax.axis("off")
    ax.set_title(f"20 genes queried independently. {len(top_genes)} came back with the "
                 f"same paper.", fontsize=11, loc="left")
    fig.tight_layout(); fig.savefig(OUT / "fig4_retrieval.png"); plt.close(fig)
    return len(top_genes)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    S = pd.read_csv(FROZEN / "program_summary.csv")
    M = pd.read_csv(FROZEN / "matrix.csv", index_col=0)
    prov = json.loads((FROZEN / "provenance.json").read_text())
    fig1(S, M); print("fig1_matrix.png")
    fig2(S); print("fig2_gate_failure.png")
    fig3(S, prov); print("fig3_measurability.png")
    n = fig4(); print(f"fig4_retrieval.png  (top source shared by {n} genes)")


if __name__ == "__main__":
    main()
