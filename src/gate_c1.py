"""Gate C1, criterion 1 (measurability). Runs exactly the pre-registered tests.

    .venv/bin/python <this file>

Not pipeline code: it computes the three gate statistics and nothing else.
No scoring, no ranking, no reversal map.
"""
from __future__ import annotations

import json
from pathlib import Path

import h5py
import numpy as np
from scipy.stats import mannwhitneyu

GMT_DIR = Path("data/genesets")   # in-repo; was an absolute scratchpad path
FILES = {
    "K562": "data/raw/K562_gwps_normalized_bulk_01.h5ad",
    "RPE1": "data/raw/rpe1_normalized_bulk_01.h5ad",
}

# locked in GATE_C1_PREREGISTRATION.md (sha256 d7d90e41...)
PROGRAMS = {
    "P1_integrated_stress_response": {
        "hallmark": "ABSENT",
        "primary": "GOBP_INTEGRATED_STRESS_RESPONSE_SIGNALING",
        "secondary": ["REACTOME_PERK_REGULATES_GENE_EXPRESSION",
                      "REACTOME_ATF4_ACTIVATES_GENES_IN_RESPONSE_TO_ENDOPLASMIC_RETICULUM_STRESS"],
    },
    "P2_senescence": {
        "hallmark": "ABSENT",
        "primary": "REACTOME_CELLULAR_SENESCENCE",
        "secondary": ["GOBP_CELLULAR_SENESCENCE",
                      "REACTOME_SENESCENCE_ASSOCIATED_SECRETORY_PHENOTYPE_SASP"],
    },
    "P3_interferon_response": {
        "hallmark": "PRESENT",
        "primary": "HALLMARK_INTERFERON_ALPHA_RESPONSE",
        "secondary": ["HALLMARK_INTERFERON_GAMMA_RESPONSE"],
    },
    "P4_proteostasis": {
        "hallmark": "PARTIAL",
        "primary": "HALLMARK_UNFOLDED_PROTEIN_RESPONSE",
        "secondary": ["REACTOME_PROTEIN_FOLDING",
                      "GOBP_PROTEASOMAL_PROTEIN_CATABOLIC_PROCESS"],
    },
}
MIN_FRAC, MIN_N, ALPHA = 0.50, 25, 0.05


def load_gmts() -> dict[str, list[str]]:
    sets: dict[str, list[str]] = {}
    for gmt in GMT_DIR.glob("*.v2026.1.Hs.symbols.gmt"):
        for line in gmt.read_text().splitlines():
            p = line.split("\t")
            if len(p) > 2:
                sets[p[0]] = p[2:]
    return sets


def load_cell(path: str) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return (gene symbols, per-gene absolute expression, per-gene SD across perturbations)."""
    with h5py.File(path, "r") as f:
        cats = [c.decode() if isinstance(c, bytes) else c
                for c in f["var/__categories/gene_name"][:]]
        codes = f["var/gene_name"][:]
        symbols = np.array([cats[c] if 0 <= c < len(cats) else "" for c in codes])
        expr = f["var/mean"][:].astype(float)
        X = f["X"][:]
    X[~np.isfinite(X)] = np.nan
    sd = np.nanstd(X, axis=0)
    return symbols, expr, sd


def contrast(members: np.ndarray, bg: np.ndarray) -> dict:
    m = members[np.isfinite(members)]
    b = bg[np.isfinite(bg)]
    med_m, med_b = float(np.median(m)), float(np.median(b))
    p = float(mannwhitneyu(m, b, alternative="greater").pvalue)
    return {"median_members": med_m, "median_background": med_b,
            "ratio": med_m / med_b if med_b else float("nan"), "p": p,
            "pass": bool(med_m / med_b >= 1.0 and p < ALPHA)}


def main() -> None:
    gmts = load_gmts()
    cells = {k: load_cell(v) for k, v in FILES.items()}
    out: dict = {"thresholds": {"min_frac": MIN_FRAC, "min_n": MIN_N, "alpha": ALPHA},
                 "shapes": {}, "programs": {}}
    for cell, path in FILES.items():
        with h5py.File(path, "r") as f:
            out["shapes"][cell] = list(f["X"].shape)

    for prog, spec in PROGRAMS.items():
        entry = {"hallmark_status": spec["hallmark"], "sets": {}}
        for role, name in ([("primary", spec["primary"])]
                           + [("secondary", s) for s in spec["secondary"]]):
            if name not in gmts:
                entry["sets"][name] = {"role": role, "error": "SET NOT FOUND"}
                continue
            members = set(gmts[name])
            rec = {"role": role, "n_declared": len(members), "cells": {}}
            for cell, (symbols, expr, sd) in cells.items():
                idx = np.where(np.isin(symbols, list(members)))[0]
                n, frac = len(idx), len(idx) / len(members)
                bg_expr = np.delete(expr, idx)
                bg_sd = np.delete(sd, idx)
                a = {"n_present": int(n), "frac_present": round(frac, 4),
                     "pass_1a": bool(frac >= MIN_FRAC and n >= MIN_N)}
                if n >= 3:
                    a["expr"] = contrast(expr[idx], bg_expr)
                    a["sd"] = contrast(sd[idx], bg_sd)
                    a["measurable"] = bool(a["pass_1a"] and a["expr"]["pass"] and a["sd"]["pass"])
                else:
                    a["measurable"] = False
                rec["cells"][cell] = a
            rec["criterion1_both_cells"] = bool(
                all(rec["cells"][c].get("measurable") for c in FILES))
            entry["sets"][name] = rec
        entry["criterion1_PRIMARY"] = entry["sets"][spec["primary"]].get(
            "criterion1_both_cells", False)
        out["programs"][prog] = entry

    Path(GMT_DIR / "gate_c1_criterion1.json").write_text(json.dumps(out, indent=2))

    # ---- console report ----
    print(f"{'program':34s} {'set':58s} {'cell':5s} {'n/decl':>11s} {'frac':>6s} "
          f"{'1a':>3s} {'exprR':>6s} {'exprP':>9s} {'1b':>3s} {'sdR':>6s} {'sdP':>9s} {'1c':>3s}")
    print("-" * 165)
    for prog, e in out["programs"].items():
        for name, rec in e["sets"].items():
            if "error" in rec:
                print(f"{prog:34s} {name:58s} !! {rec['error']}")
                continue
            for cell, a in rec["cells"].items():
                if "expr" not in a:
                    print(f"{prog:34s} {name:58s} {cell:5s} too few members")
                    continue
                print(f"{prog:34s} {name:58s} {cell:5s} "
                      f"{a['n_present']:4d}/{rec['n_declared']:<6d} {a['frac_present']:6.3f} "
                      f"{'Y' if a['pass_1a'] else 'N':>3s} "
                      f"{a['expr']['ratio']:6.2f} {a['expr']['p']:9.2e} "
                      f"{'Y' if a['expr']['pass'] else 'N':>3s} "
                      f"{a['sd']['ratio']:6.2f} {a['sd']['p']:9.2e} "
                      f"{'Y' if a['sd']['pass'] else 'N':>3s}")
        print(f"  => {prog}: CRITERION 1 (primary set, both cells) = "
              f"{'PASS' if e['criterion1_PRIMARY'] else 'FAIL'}\n")


if __name__ == "__main__":
    main()
