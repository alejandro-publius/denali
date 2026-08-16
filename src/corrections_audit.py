"""Do the published fixes for the size confound actually work on real screens?

Pre-registered in docs/CORRECTIONS_PREREG.md (sha256 d58fa082..., committed
a2776f7 BEFORE the substrate was downloaded). The correction list, the metrics,
the verdict thresholds and the obligation to report denali's own correction
losing to a published method are all fixed there and are not revised here.

Substrate: BioGRID ORCS 2.0.18 (the same tarball, byte count verified
752,653,348) x MSigDB Hallmark v2026.1.Hs. Inclusion rule verbatim from
src/corpus_audit.py: >= 20 hits, >= 10,000 genes measured, >= 8 usable sets
(>= 5 measured members).

GATE, run before any correction number is read: the per-screen size-alone R^2
(log-size predictor, the corpus transform) must reproduce the committed
results/corpus/corpus_per_screen.csv on >= 99% of matching screen IDs within
+/-0.0005, or this script stops and reports the discrepancy instead.

Corrections (IDs from the pre-registration):
  C0  none               rank sets by hit count k              (the audited baseline)
  C1  ORA hypergeometric -log10 upper-tail p                   (the field's default)
  C2  size-preserving permutation null, standardized: for binary hit data this
      IS the hypergeometric z = (k - E[k])/sd[k], computed analytically; the
      identity is the point, not a shortcut
  C3  competitive score test, CAMERA at rho=0 (= two-sample z on SCORE.1); also
      what MAGMA's competitive regression reduces to absent per-gene covariates
  C4  CAMERA VIF-inflated competitive test, rho = 0.01 and 0.05 (fixed; typical
      values discussed by Wu & Smyth 2012, doi:10.1093/nar/gks461). Inter-gene
      correlations are NOT computable from ORCS hit tables; fixed rho is the
      arm's main limitation and was declared in the pre-registration
  C5  denali's own residualisation (core.rerank verbatim): residual of
      log10(1+k) on raw m

Declared N/A in the pre-registration, not decided here: GOseq (corrects a
per-gene covariate, not set size), SetRank (corrects inter-set overlap).

Primary metric per screen x correction: squared Spearman correlation between
the ranked statistic and set size. Rank-based because the corrections emit
statistics on incomparable scales, and because it does not hand C5 a win by
construction.

Writes results/corrections/per_screen.csv and results/corrections/summary.json.
Names no screen, publication or gene set as a finding: the unit of inference
is the distribution.

    .venv/bin/python -m src.corrections_audit
"""
from __future__ import annotations

import glob
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import hypergeom, spearmanr

GMT = Path("data/genesets/h.all.v2026.1.Hs.symbols.gmt")
RAW = Path("data/raw/orcs")
COMMITTED = Path("results/corpus/corpus_per_screen.csv")
OUTDIR = Path("results/corrections")

RHO_VALUES = (0.01, 0.05)          # fixed in the pre-registration
BEFORE_FLOOR = 0.05                # relative reduction defined only above this
WORSE_MARGIN = 0.05                # "made it worse" = after > before + this
SCORE_COVERAGE = 0.80              # C3/C4 need SCORE.1 finite on >= this share

CORRECTIONS = ["C1_hypergeom", "C2_perm_z", "C3_camera_rho0",
               "C4_vif_rho01", "C4_vif_rho05", "C5_residual"]


def load_gmt(path: Path) -> dict[str, set[str]]:
    sets = {}
    for line in path.read_text().splitlines():
        if line.strip():
            f = line.split("\t")
            sets[f[0]] = set(f[2:])
    return sets


def r2_linear(x, y) -> float:
    x, y = np.asarray(x, float), np.asarray(y, float)
    if len(x) < 8 or np.allclose(y, y[0]) or np.allclose(x, x[0]):
        return float("nan")
    X = np.column_stack([np.ones(len(x)), x])
    b, *_ = np.linalg.lstsq(X, y, rcond=None)
    p = X @ b
    return float(1 - ((y - p) ** 2).sum() / ((y - y.mean()) ** 2).sum())


def rho2(stat, m) -> float:
    s = np.asarray(stat, float)
    if np.all(s == s[0]):
        return float("nan")
    r = spearmanr(s, m).statistic
    return float(r * r) if np.isfinite(r) else float("nan")


def top10_overlap(base_stat, stat) -> int:
    b = set(np.argsort(-np.asarray(base_stat), kind="stable")[:10])
    s = set(np.argsort(-np.asarray(stat), kind="stable")[:10])
    return len(b & s)


def audit_one(m, k, M, H, scores_in_mean, scores_all_mean, scores_all_sd,
              m_scored, M_scored) -> dict[str, np.ndarray]:
    """All correction statistics for one screen. m,k arrays over usable sets."""
    m = np.asarray(m, float)
    k = np.asarray(k, float)
    out = {"C0_hits": k}

    p = hypergeom.sf(k - 1, M, H, m)
    out["C1_hypergeom"] = -np.log10(np.maximum(p, 1e-300))

    frac = H / M
    var = m * frac * (1 - frac) * (M - m) / (M - 1)
    sd = np.sqrt(var)
    with np.errstate(invalid="ignore", divide="ignore"):
        z = np.where(sd > 0, (k - m * frac) / sd, 0.0)
    out["C2_perm_z"] = z

    if scores_in_mean is not None:
        ms = np.asarray(m_scored, float)
        delta = np.asarray(scores_in_mean, float) - (
            (scores_all_mean * M_scored - np.asarray(scores_in_mean, float) * ms)
            / (M_scored - ms))
        with np.errstate(invalid="ignore", divide="ignore"):
            base_se = scores_all_sd * np.sqrt(1 / ms + 1 / (M_scored - ms))
            out["C3_camera_rho0"] = np.abs(np.where(base_se > 0, delta / base_se, 0.0))
            for rho, name in zip(RHO_VALUES, ["C4_vif_rho01", "C4_vif_rho05"]):
                vif = 1 + (ms - 1) * rho
                se = scores_all_sd * np.sqrt(vif / ms + 1 / (M_scored - ms))
                out[name] = np.abs(np.where(se > 0, delta / se, 0.0))

    y = np.log10(1 + k)
    if np.std(m) == 0:
        out["C5_residual"] = y - y.mean()
    else:
        b = np.polyfit(m, y, 1)
        out["C5_residual"] = y - np.polyval(b, m)
    return out


def main() -> int:
    sets = load_gmt(GMT)
    idx_path = glob.glob(str(RAW / "*index.tab.txt"))[0]
    idx = pd.read_csv(idx_path, sep="\t", low_memory=False)
    idx.columns = [c.lstrip("#") for c in idx.columns]
    idx["SCREEN_ID"] = idx["SCREEN_ID"].astype(str)
    meta = idx.set_index("SCREEN_ID")

    committed = pd.read_csv(COMMITTED, dtype={"screen_id": str}).set_index("screen_id")

    rows = []
    n_parse_failed = n_excluded = 0
    files = sorted(glob.glob(str(RAW / "*screen.tab.txt")))
    for i, f in enumerate(files):
        if i % 400 == 0:
            print(f"  {i}/{len(files)}")
        try:
            d = pd.read_csv(f, sep="\t",
                            usecols=["#SCREEN_ID", "OFFICIAL_SYMBOL", "HIT", "SCORE.1"],
                            low_memory=False)
        except Exception:
            n_parse_failed += 1
            continue
        if not len(d):
            n_parse_failed += 1
            continue
        sid = str(d["#SCREEN_ID"].iloc[0])
        hits = set(d.loc[d.HIT.astype(str).str.upper() == "YES", "OFFICIAL_SYMBOL"].dropna())
        measured = set(d.OFFICIAL_SYMBOL.dropna())
        if len(hits) < 20 or len(measured) < 10000:
            n_excluded += 1
            continue

        score = pd.to_numeric(d["SCORE.1"], errors="coerce")
        sc = d.assign(score=score).dropna(subset=["OFFICIAL_SYMBOL"])
        by_gene = sc.groupby("OFFICIAL_SYMBOL")["score"].mean()
        finite = by_gene[np.isfinite(by_gene)]
        has_scores = len(finite) >= SCORE_COVERAGE * len(measured)
        if has_scores:
            M_scored = len(finite)
            all_mean = float(finite.mean())
            all_sd = float(finite.std(ddof=1))
            if not np.isfinite(all_sd) or all_sd == 0:
                has_scores = False

        m_v, k_v, in_mean_v, m_scored_v, names = [], [], [], [], []
        for name, g in sets.items():
            mem = g & measured
            if len(mem) < 5:
                continue
            m_v.append(len(mem))
            k_v.append(len(g & hits))
            names.append(name)
            if has_scores:
                s_in = finite.reindex(list(mem)).dropna()
                m_scored_v.append(len(s_in))
                in_mean_v.append(float(s_in.mean()) if len(s_in) else np.nan)
        if len(m_v) < 8:
            n_excluded += 1
            continue

        m_a, k_a = np.array(m_v, float), np.array(k_v, float)
        gate_v = r2_linear(np.log10(m_a), np.log10(1 + k_a))
        if not np.isfinite(gate_v):
            n_excluded += 1
            continue

        score_ok = has_scores and all(np.isfinite(in_mean_v)) and \
            all(np.array(m_scored_v) >= 3) and \
            (np.array(m_scored_v) < M_scored).all()
        stats = audit_one(
            m_a, k_a, len(measured), len(hits),
            in_mean_v if score_ok else None, all_mean if score_ok else None,
            all_sd if score_ok else None, m_scored_v if score_ok else None,
            M_scored if score_ok else None)

        before = rho2(stats["C0_hits"], m_a)
        row = {
            "screen_id": sid,
            "gate_r2_logsize": round(gate_v, 4),
            "n_sets_used": len(m_a),
            "has_scores": bool(score_ok),
            "before_rho2": round(before, 4) if np.isfinite(before) else np.nan,
            "before_r2_linear": round(r2_linear(m_a, np.log10(1 + k_a)), 4),
            "source_id": str(meta.loc[sid]["SOURCE_ID"]) if sid in meta.index else "",
        }
        for c in CORRECTIONS:
            if c in stats:
                after = rho2(stats[c], m_a)
                row[f"{c}_rho2"] = round(after, 4) if np.isfinite(after) else np.nan
                row[f"{c}_top10"] = top10_overlap(stats["C0_hits"], stats[c])
                lin = r2_linear(m_a, stats[c])
                row[f"{c}_r2_linear"] = round(lin, 4) if np.isfinite(lin) else np.nan
        rows.append(row)

    R = pd.DataFrame(rows)
    print(f"\nfiles: {len(files)}  parse-failed: {n_parse_failed}  "
          f"excluded: {n_excluded}  audited: {len(R)}")

    # ---- GATE: reproduce the committed corpus numbers before reading anything
    joined = R.set_index("screen_id").join(committed[["r2_size_alone"]], how="inner")
    agree = (joined.gate_r2_logsize - joined.r2_size_alone).abs() <= 0.0005
    gate_pct = 100 * agree.mean()
    print(f"GATE: {len(joined)} matching screens, {gate_pct:.2f}% within 0.0005")
    gate = {"n_matching": int(len(joined)), "pct_within_tol": round(float(gate_pct), 2),
            "passed": bool(gate_pct >= 99.0)}
    OUTDIR.mkdir(parents=True, exist_ok=True)
    if not gate["passed"]:
        (OUTDIR / "summary.json").write_text(json.dumps(
            {"status": "GATE FAILED — no correction result is reported",
             "gate": gate}, indent=2) + "\n")
        R.to_csv(OUTDIR / "per_screen.csv", index=False)
        print("GATE FAILED — stopping before any correction number is read.")
        return 1

    # ---- verdicts, thresholds fixed in the pre-registration
    def aggregate(sub: pd.DataFrame, c: str) -> dict:
        ok = sub.dropna(subset=["before_rho2", f"{c}_rho2"])
        el = ok[ok.before_rho2 >= BEFORE_FLOOR]
        relred = 1 - el[f"{c}_rho2"] / el.before_rho2
        worse = (ok[f"{c}_rho2"] > ok.before_rho2 + WORSE_MARGIN)
        pub_rel = (1 - ok[f"{c}_rho2"] / ok.before_rho2)[ok.before_rho2 >= BEFORE_FLOOR] \
            .groupby(ok.source_id).median()
        d = {
            "n_screens": int(len(ok)),
            "n_above_floor": int(len(el)),
            "median_relative_reduction": round(float(relred.median()), 4),
            "relative_reduction_q25_q75": [round(float(relred.quantile(q)), 4)
                                           for q in (0.25, 0.75)],
            "worse_share_pct": round(100 * float(worse.mean()), 2),
            "median_after_rho2": round(float(ok[f"{c}_rho2"].median()), 4),
            "median_top10_overlap": float(ok[f"{c}_top10"].median()),
            "publication_level_median_relative_reduction":
                round(float(pub_rel.median()), 4) if len(pub_rel) else None,
        }
        mr, ws = d["median_relative_reduction"], d["worse_share_pct"]
        if mr >= 0.50 and ws <= 5:
            d["verdict"] = "WORKS"
        elif mr >= 0.50:
            d["verdict"] = "WORKS ON MEDIAN, UNRELIABLE TAIL"
        elif 0.20 <= mr < 0.50 and ws <= 15:
            d["verdict"] = "PARTIAL"
        else:
            d["verdict"] = "FAILS"
        return d

    results = {}
    for c in CORRECTIONS:
        sub = R if not c.startswith(("C3", "C4")) else R[R.has_scores]
        if c.startswith(("C3", "C4")) and R.has_scores.sum() < 200:
            results[c] = {"verdict": "NO VERDICT — score sub-corpus below "
                          "pre-registered 200", "n_screens": int(R.has_scores.sum())}
            continue
        results[c] = aggregate(sub, c)

    # ---- SECONDARY, registered as descriptive: does the top of the list move?
    # The headline metric is how much size dependence survives a correction.
    # That is not the same question as whether the sets a biologist would
    # actually chase change places, and the two answers differ sharply, so
    # both are reported. Stratified by how confounded the screen was to begin
    # with, because a correction has nothing to remove from a clean screen.
    R["stratum"] = pd.cut(R.before_rho2, [-1, 0.05, 0.10, 0.20, 1],
                          labels=["<0.05", "0.05-0.10", "0.10-0.20", ">0.20"])
    top10 = {}
    for c in CORRECTIONS:
        col = f"{c}_top10"
        if col not in R:
            continue
        sub = R if not c.startswith(("C3", "C4")) else R[R.has_scores]
        g = sub.groupby("stratum", observed=True)[col].median()
        top10[c] = {"overall_median_overlap": float(sub[col].median()),
                    "by_baseline_confound": {str(k): float(v) for k, v in g.items()}}
    strata_n = {str(k): int(v) for k, v in
                R.stratum.value_counts().sort_index().items()}

    summary = {
        "status": "Pre-registered in docs/CORRECTIONS_PREREG.md "
                  "(d58fa082..., commit a2776f7).",
        "substrate": "BioGRID ORCS 2.0.18 (752,653,348 bytes verified) x "
                     "Hallmark v2026.1.Hs; inclusion verbatim from src/corpus_audit.py",
        "gate": gate,
        "n_screens_audited": int(len(R)),
        "n_with_usable_scores": int(R.has_scores.sum()),
        "before_rho2_median": round(float(R.before_rho2.median()), 4),
        "primary_metric": "squared Spearman correlation of ranked statistic vs set size",
        "corrections": results,
        "top10_overlap_with_uncorrected_ranking": {
            "why": "Hit counts are small integers with heavy ties, so the top "
                   "of a Hallmark ranking is often tie-determined. A correction "
                   "can collapse the size dependence while leaving the same "
                   "sets at the top -- and in the screens where the confound is "
                   "weakest that is exactly what happens. Where the baseline "
                   "confound is strongest, the top ten does move.",
            "n_screens_per_stratum": strata_n,
            "by_correction": top10,
        },
        "caveat": "Driving the size correlation to zero proves size-decoupling, "
                  "not correctness; a correction that deleted all biology would "
                  "also score perfectly here. No ground truth exists in this corpus.",
        "not_applicable": {
            "GOseq": "corrects a per-gene covariate (transcript length), not set size",
            "SetRank": "corrects inter-set overlap, not size; faithful "
                       "implementation out of scope"},
    }
    (OUTDIR / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    R.to_csv(OUTDIR / "per_screen.csv", index=False)
    print(json.dumps({c: results[c].get("verdict") for c in results}, indent=2))
    print(f"wrote {OUTDIR}/summary.json and {OUTDIR}/per_screen.csv")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
