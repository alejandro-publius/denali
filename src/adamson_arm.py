"""Adamson 2016 arm — does the size confound survive when the program is ENGAGED?

PRE-REGISTERED. Thresholds fixed in docs/ADAMSON_PREREG.md (sha256 4a7ece03…,
committed at 7a98d4d) BEFORE this file existed or any Adamson value was computed.

    P0 engagement fails                       -> PREMISE NOT ESTABLISHED, no verdict
    fewer than 35 of 50 scoreable             -> UNDERPOWERED, no verdict
    fewer than 15 of 50 with >=1 hit          -> UNDERPOWERED, no verdict
    size-alone R2 >= 0.25 and positive slope  -> confound persists under engagement
    0.10 <= R2 < 0.25                         -> inconclusive
    R2 < 0.10 or negative slope               -> does not persist; narrow the headline

denali records its own design failure: K562 is unstressed, so the UPR was never
switched on, and the gate tested whether a program was MEASURABLE when it should
have tested whether it was ENGAGED. Adamson is a UPR Perturb-seq screen in the
same cell line, built to induce ER stress. This is that test.

SCOPE: a targeted UPR library of ~115 perturbations is NOT a genome-scale screen
and this arm is NOT a replication of the K562 result.

The byte-frozen scorer's score() is imported and called UNMODIFIED. The
single-cell -> perturbation-effect construction below is NEW code and is NOT
covered by the scorer's hash; that is disclosed rather than folded into a claim
of having used the identical pipeline. Writes results/adamson/ ONLY;
results/frozen/ is not touched.

    .venv/bin/python -m src.adamson_arm
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import h5py
import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import sparse
from scipy.stats import norm, spearmanr
from statsmodels.stats.multitest import multipletests

from src import score_k562 as SC
from src import sweep as SW

ADAMSON = Path("data/raw/AdamsonWeissman2016_GSM2406681_10X010.h5ad")
FROZEN = Path("results/frozen")
OUT = Path("results/adamson")

PREREG_ORIGINAL_SHA = "4a7ece0376e2aac0433277d5dd7bd891bcaabf347d0c7505cb3e5859643101d9"
# Amendment 1 (2026-08-15) appended BELOW the original text; no threshold moved.
# The original is diffable at 7a98d4d under the hash above.
PREREG_SHA = "b83e7308a62e041c2096bd6625ce7c46c086525346ec8b22f3e22fa54e361fb5"
SCORER_SHA = "2abfdc6f730d786180e37f73e2951c303c5a7b42caa27dc3394c74c323d7bbfa"

# every one of these is from docs/ADAMSON_PREREG.md and none may move
R2_PERSISTS = 0.25
R2_FLOOR = 0.10
MIN_SCOREABLE = 35          # P1
MIN_WITH_HITS = 15          # P2
MIN_CELLS_PER_PERT = 25
MIN_GENE_DETECT_FRAC = 0.01
COUNTS_PER_CELL = 1e4
N_NULL = 1000               # P0
P0_PERCENTILE = 99.0
SEED = 0

# Amendment 1: control is defined by CONSTRUCT IDENTITY, not by picking a label
# after seeing the data. All 100 targeting guides are GENE_pDS###; of the 13 pBA
# constructs, 10 name a human UPR gene. The rest carry (mod) and name no human
# gene -- Gal4 is a yeast TF with no human homolog. Controls are POOLED.
def _is_control(label: str) -> bool:
    return "(mod)" in label and "_pBA" in label


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _decode(f: h5py.File, grp: str, key: str) -> np.ndarray:
    """Read an anndata column as strings, whatever encoding it uses.

    anndata has written categoricals three ways across versions: a group with
    codes+categories, an int dataset paired with <grp>/__categories/<key>, or a
    plain string dataset. Guessing wrong here silently joins on integers.
    """
    node = f[f"{grp}/{key}"]
    if isinstance(node, h5py.Group):
        cats = [c.decode() if isinstance(c, bytes) else str(c)
                for c in node["categories"][:]]
        codes = node["codes"][:]
        return np.array([cats[c] if 0 <= c < len(cats) else "" for c in codes],
                        dtype=object)
    catpath = f"{grp}/__categories/{key}"
    if catpath in f:
        cats = [c.decode() if isinstance(c, bytes) else str(c)
                for c in f[catpath][:]]
        codes = node[:]
        return np.array([cats[c] if 0 <= c < len(cats) else "" for c in codes],
                        dtype=object)
    return np.array([x.decode() if isinstance(x, bytes) else str(x)
                     for x in node[:]], dtype=object)


def _index_key(f: h5py.File, grp: str) -> str:
    a = f[grp].attrs
    for k in ("_index", "index"):
        if k in a:
            v = a[k]
            return v.decode() if isinstance(v, bytes) else str(v)
    return "_index"


def load_substrate() -> dict:
    """Sparse counts -> perturbation-effect matrix, exactly as pre-registered."""
    with h5py.File(ADAMSON, "r") as f:
        Xg = f["X"]
        enc = Xg.attrs.get("encoding-type", b"")
        enc = enc.decode() if isinstance(enc, bytes) else str(enc)
        shape = tuple(int(x) for x in Xg.attrs["shape"])
        M = (sparse.csc_matrix if "csc" in enc else sparse.csr_matrix)(
            (Xg["data"][:].astype(np.float32), Xg["indices"][:], Xg["indptr"][:]),
            shape=shape)

        vkey = _index_key(f, "var")
        gene_field = next((k for k in ("gene_symbol", "gene_name", "gene_symbols")
                           if k in f["var"]), vkey)
        symbols = _decode(f, "var", gene_field)
        pert = _decode(f, "obs", "perturbation")

    M = M.tocsr()
    n_cells, n_genes = M.shape

    # 1. genes detected in >= 1% of cells
    detect = np.asarray((M > 0).sum(axis=0)).ravel()
    keep = detect >= (MIN_GENE_DETECT_FRAC * n_cells)
    M, symbols = M[:, keep], symbols[keep]

    # 2. normalise each cell to 10,000 counts over the retained genes, then log1p
    tot = np.asarray(M.sum(axis=1)).ravel()
    tot[tot == 0] = 1.0
    M = sparse.diags((COUNTS_PER_CELL / tot).astype(np.float32)) @ M
    M.data = np.log1p(M.data)

    # 3-4. pseudobulk per construct, >= 25 cells. The floor is the ORIGINAL
    # pre-registered one and applies to controls too -- 62(mod)_pBA581 has 2
    # cells and is excluded by it, not by anything added after the fact.
    labels = pd.Series(pert)
    uniq = list(labels.unique())
    counts = labels.value_counts()
    kept = [u for u in uniq if counts[u] >= MIN_CELLS_PER_PERT]
    dropped = sorted(str(u) for u in uniq if counts[u] < MIN_CELLS_PER_PERT)

    controls = [u for u in kept if _is_control(str(u))]
    excluded_ctrl = [str(u) for u in uniq
                     if _is_control(str(u)) and u not in kept]
    if not controls:
        raise SystemExit(
            "NOT RUNNABLE: no (mod)_pBA control construct survives the "
            f"{MIN_CELLS_PER_PERT}-cell floor. The pre-registration forbids "
            "relaxing this step.")

    order = {u: i for i, u in enumerate(kept)}
    col = np.array([order.get(u, -1) for u in labels])
    sel = col >= 0
    G = sparse.csr_matrix(
        (1.0 / counts[labels[sel]].values.astype(np.float64),
         (col[sel], np.nonzero(sel)[0])), shape=(len(kept), n_cells))
    PB = np.asarray((G @ M).todense())

    # 5. POOLED control (Amendment 1): cell-weighted mean over the control
    # constructs, i.e. the mean over the pooled control cells.
    w = np.array([counts[c] for c in controls], dtype=np.float64)
    pooled = (np.vstack([PB[order[c]] for c in controls]) * w[:, None]).sum(0) / w.sum()

    rows = [u for u in kept if u not in set(controls)]
    Xt = np.vstack([PB[order[u]] for u in rows])

    def _effect(ref):
        E = Xt - ref
        E[~np.isfinite(E)] = np.nan          # 6. mask, never impute
        return E

    return {"X": _effect(pooled), "symbols": np.asarray(symbols, dtype=object),
            "perturbations": np.array([str(u) for u in rows], dtype=object),
            "control_labels": [str(c) for c in controls],
            "control_definition": "(mod) AND _pBA — construct identity, Amendment 1",
            "control_expr": pooled,
            "single_control_effects": {
                str(c): _effect(PB[order[c]]) for c in controls},
            "n_cells": int(n_cells), "n_genes_raw": int(n_genes),
            "n_genes_kept": int(keep.sum()), "gene_field": gene_field,
            "encoding": enc,
            "n_cells_control_pooled": int(w.sum()),
            "n_cells_per_control": {str(c): int(counts[c]) for c in controls},
            "control_constructs_excluded_by_cell_floor": excluded_ctrl,
            "dropped_perturbations": dropped,
            "median_cells_per_perturbation": float(counts[kept].median())}


def engagement_p0(X, symbols, control_expr, program) -> dict:
    """P0 — is the UPR actually engaged here? Null matched on size AND decile."""
    rng = np.random.default_rng(SEED)
    idx = np.where(np.isin(symbols, program))[0]
    if len(idx) < 2:
        return {"established": False, "reason": "fewer than 2 program genes measured",
                "n_measured": int(len(idx))}

    absX = np.abs(X)
    observed = float(np.nanmean(absX[:, idx]))

    # decile by absolute expression in the unperturbed control
    dec = pd.qcut(pd.Series(control_expr), 10, labels=False, duplicates="drop").values
    want = pd.Series(dec[idx]).value_counts().to_dict()
    pool = {d: np.setdiff1d(np.where(dec == d)[0], idx) for d in want}
    for d, n in want.items():
        if len(pool[d]) < n:
            return {"established": False,
                    "reason": f"decile {d} has {len(pool[d])} non-program genes, "
                              f"cannot match {n}", "n_measured": int(len(idx))}

    null = np.empty(N_NULL)
    for i in range(N_NULL):
        pick = np.concatenate([rng.choice(pool[d], n, replace=False)
                               for d, n in want.items()])
        null[i] = np.nanmean(absX[:, pick])
    thresh = float(np.percentile(null, P0_PERCENTILE))
    # one-sided empirical p, +1 smoothing so p is never reported as exactly 0
    p = float((np.sum(null >= observed) + 1) / (N_NULL + 1))
    return {"established": bool(observed > thresh), "observed_mean_abs_effect":
            round(observed, 6), "null_p99": round(thresh, 6),
            "null_mean": round(float(null.mean()), 6), "empirical_p": p,
            "n_measured": int(len(idx)), "n_null_sets": N_NULL, "seed": SEED,
            "matched_on": "set size and control-expression decile"}


def score_programs(X, symbols, sets, progress=False) -> pd.DataFrame:
    """Score all 50 Hallmark programs with the frozen scorer, unmodified."""
    rows = []
    for i, (name, program) in enumerate(sorted(sets.items()), 1):
        u_z, cos, delta, n_present = SC.score(X, symbols, program)
        p = 2 * norm.sf(np.abs(u_z))
        ok = np.isfinite(p)
        q = np.full_like(p, np.nan)
        if ok.sum():
            q[ok] = multipletests(p[ok], method="fdr_bh")[1]
        n_hits = int(np.nansum(q < SW.ALPHA))
        rows.append({"program": name, "n_declared": len(program),
                     "n_present": n_present,
                     "frac_present": round(n_present / len(program), 4),
                     "n_hits_q05": n_hits,
                     "R_p": round(float(np.log10(1 + n_hits)), 4),
                     "scoreable": bool(n_present >= 2 and np.isfinite(u_z).any())})
        if progress and i % 10 == 0:
            print(f"  {i}/50 …")
    return pd.DataFrame(rows)


def fit_size(d: pd.DataFrame) -> dict:
    """The deciding statistic: R2 of R_p on n_present alone, OLS, one predictor."""
    fit = sm.OLS(d.R_p, sm.add_constant(d.n_present)).fit()
    return {"size_alone_r2": round(float(fit.rsquared), 4),
            "slope": round(float(fit.params.iloc[1]), 6),
            "slope_p": float(f"{fit.pvalues.iloc[1]:.4g}"),
            "n_scoreable": int(len(d))}


def main() -> None:
    # The scorer must be the frozen one; the pre-registration says abandon rather
    # than edit. Same for the pre-registration itself.
    actual = _sha(Path("src/score_k562.py"))
    if actual != SCORER_SHA:
        raise SystemExit(f"scorer hash {actual[:16]} != frozen {SCORER_SHA[:16]}; "
                         "the pre-registration forbids editing it. Arm abandoned.")
    pre = _sha(Path("docs/ADAMSON_PREREG.md"))
    if pre != PREREG_SHA:
        raise SystemExit(f"pre-registration changed ({pre[:16]}). Thresholds may "
                         "not be revised after the fact. Arm abandoned.")

    sub = load_substrate()
    X, symbols = sub["X"], sub["symbols"]
    print(f"Adamson substrate: {sub['n_cells']:,} cells x {sub['n_genes_raw']:,} "
          f"genes -> {sub['n_genes_kept']:,} kept")
    print(f"  control (pooled) : {sub['control_labels']} "
          f"= {sub['n_cells_control_pooled']:,} cells")
    if sub["control_constructs_excluded_by_cell_floor"]:
        print(f"  excluded by the {MIN_CELLS_PER_PERT}-cell floor: "
              f"{sub['control_constructs_excluded_by_cell_floor']}")
    print(f"  effect matrix    : {X.shape[0]} perturbations x {X.shape[1]} genes")
    print(f"  dropped (<{MIN_CELLS_PER_PERT} cells): {len(sub['dropped_perturbations'])}")

    sets = SW.hallmark()

    # ---- P0: the premise, checked before anything else ----
    p0 = engagement_p0(X, symbols, sub["control_expr"],
                       sets["HALLMARK_UNFOLDED_PROTEIN_RESPONSE"])
    print(f"\nP0 engagement    : {'ESTABLISHED' if p0['established'] else 'FAILED'}"
          f"  observed {p0.get('observed_mean_abs_effect')} vs null p99 "
          f"{p0.get('null_p99')}  (p={p0.get('empirical_p')})")

    S = score_programs(X, symbols, sets, progress=True)
    OUT.mkdir(parents=True, exist_ok=True)
    S.to_csv(OUT / "program_summary_adamson.csv", index=False)

    d = S[S.scoreable & S.n_present.notna() & (S.n_present > 0)]
    n_scoreable = int(len(d))
    n_with_hits = int((d.n_hits_q05 > 0).sum())

    res = {
        "preregistration": {"file": "docs/ADAMSON_PREREG.md", "sha256": PREREG_SHA,
                            "committed": "7a98d4d", "committed_before_this_ran": True},
        "scorer_sha256": SCORER_SHA, "scorer_unmodified": True,
        "substrate": ADAMSON.name,
        "substrate_construction_covered_by_scorer_hash": False,
        "construction": {
            "note": "single-cell counts -> perturbation-effect matrix. NEW code, "
                    "pre-specified in the pre-registration, NOT part of the frozen "
                    "scorer. This is the arm's one real degree of freedom.",
            "gene_detect_frac": MIN_GENE_DETECT_FRAC,
            "counts_per_cell": COUNTS_PER_CELL,
            "min_cells_per_perturbation": MIN_CELLS_PER_PERT,
            "control_definition": sub["control_definition"],
            "control_labels": sub["control_labels"],
            "n_cells_control_pooled": sub["n_cells_control_pooled"],
            "n_cells_per_control": sub["n_cells_per_control"],
            "control_constructs_excluded_by_cell_floor":
                sub["control_constructs_excluded_by_cell_floor"],
            "gene_field": sub["gene_field"], "encoding": sub["encoding"],
            "n_cells": sub["n_cells"], "n_genes_raw": sub["n_genes_raw"],
            "n_genes_kept": sub["n_genes_kept"],
            "n_perturbations": int(X.shape[0]),
            "median_cells_per_perturbation": sub["median_cells_per_perturbation"],
            "dropped_perturbations": sub["dropped_perturbations"],
        },
        "preregistration_amendment": {
            "amendment": 1, "date": "2026-08-15",
            "original_sha256": PREREG_ORIGINAL_SHA, "original_commit": "7a98d4d",
            "what_changed": "Resolved which construct is the control, by a rule "
                            "about construct identity ((mod) AND _pBA, pooled), "
                            "appended BELOW the original text.",
            "thresholds_changed": "none — P0, P1, P2 and the R2 bands are "
                                  "untouched and the original is diffable",
        },
        "p0_engagement": p0,
        "n_programs": len(S), "n_scoreable": n_scoreable,
        "n_with_at_least_one_hit": n_with_hits,
        "n_zero_hit_programs": int((d.n_hits_q05 == 0).sum()),
    }

    # ---- the pre-registered decision ladder, in order ----
    if not p0["established"]:
        res.update(verdict="PREMISE NOT ESTABLISHED", claim_supported=None,
                   reason="P0 failed: the UPR is not detectably engaged in this "
                          "substrate above a size- and expression-matched null, so "
                          "the arm's premise does not hold and no verdict on (a)/(b) "
                          "is issued.")
    elif n_scoreable < MIN_SCOREABLE:
        res.update(verdict="UNDERPOWERED AND INCONCLUSIVE", claim_supported=None,
                   reason=f"P1 fired: only {n_scoreable} of {len(S)} scoreable, "
                          f"pre-registered floor {MIN_SCOREABLE}.")
    elif n_with_hits < MIN_WITH_HITS:
        res.update(verdict="UNDERPOWERED AND INCONCLUSIVE", claim_supported=None,
                   reason=f"P2 fired: only {n_with_hits} of {len(S)} scoreable "
                          f"programs returned any hit, pre-registered floor "
                          f"{MIN_WITH_HITS}. R_p is degenerate and a regression on "
                          f"it would not be a measurement.")
    else:
        f = fit_size(d)
        r2, slope = f["size_alone_r2"], f["slope"]
        if r2 >= R2_PERSISTS and slope > 0:
            v, c = "PERSISTS UNDER ENGAGEMENT", "(a)"
        elif r2 < R2_FLOOR or slope <= 0:
            v, c = "DOES NOT PERSIST", "(b)"
        else:
            v, c = "INCONCLUSIVE", None
        res.update(verdict=v, claim_supported=c,
                   size_alone_r2=r2, slope=slope, slope_p=f["slope_p"],
                   k562_size_alone_r2_for_reference=json.loads(
                       Path("results/sensitivity/stripped_model.json").read_text()
                   )["set_size_alone"]["r2"])

    # ---- Amendment 1 secondary: did the control choice manufacture this? ----
    # Reported whatever it says. No threshold is applied and no verdict issues
    # from it; the pooled definition remains the primary.
    sens = {}
    for lab, Xs in sub["single_control_effects"].items():
        Ss = score_programs(Xs, symbols, sets)
        ds = Ss[Ss.scoreable & (Ss.n_present > 0)]
        sens[lab] = {**fit_size(ds), "n_cells": sub["n_cells_per_control"][lab],
                     "n_with_at_least_one_hit": int((ds.n_hits_q05 > 0).sum())}
    res["control_choice_sensitivity"] = {
        "primary": "pooled non-targeting constructs, per Amendment 1",
        "note": "Reported so a reader can see the control definition did not "
                "manufacture the result. Descriptive: no threshold, no verdict.",
        "per_single_control": sens,
    }

    # ---- secondary, descriptive, no thresholds ----
    k562 = pd.read_csv(FROZEN / "program_summary.csv")
    j = d.merge(k562[["program", "R_p"]], on="program", suffixes=("", "_k562"))
    if len(j) > 2:
        rho, pv = spearmanr(j.R_p, j.R_p_k562)
        res["secondary_descriptive"] = {
            "spearman_k562_vs_adamson_R_p": round(float(rho), 4),
            "p": float(f"{pv:.4g}"), "n_programs": int(len(j)),
            "note": "Descriptive only. No threshold was set for this and none is "
                    "applied after the fact. The library designs differ by two "
                    "orders of magnitude in size and by intent.",
        }

    res["scope"] = (
        "NOT a replication of the K562 genome-scale result. Adamson is a TARGETED "
        f"UPR library of {X.shape[0]} retained perturbations against K562's 9,837 "
        "genome-scale knockdowns -- deliberately enriched for regulators of the "
        "program under test. It is the worst substrate for a claim about unbiased "
        "screens and the best available one for a claim about engagement, and it "
        "is used only for the second. The single-cell to perturbation-effect "
        "construction is new code and is NOT covered by the frozen scorer's hash.")
    res["does_not_revise"] = "the pre-registered K562 primary in results/frozen/"

    (OUT / "adamson_evaluation.json").write_text(json.dumps(res, indent=1) + "\n")

    print(f"\nscoreable            : {n_scoreable}/50")
    print(f"with >=1 hit         : {n_with_hits}/50")
    if "size_alone_r2" in res:
        print(f"size-alone R2        : {res['size_alone_r2']}   "
              f"slope {res['slope']:+.5f}  p={res['slope_p']}")
        print(f"  K562 reference     : {res['k562_size_alone_r2_for_reference']}")
    print(f"VERDICT              : {res['verdict']}")
    print(f"  {res.get('reason', '')}")
    print(f"\nwrote {OUT/'adamson_evaluation.json'}")


if __name__ == "__main__":
    main()
