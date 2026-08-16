"""Does denali's finding hold across the published CRISPR screen literature?

POST-HOC, exploratory. Nothing pre-registered. This exists to test denali's own
headline against the field rather than to confirm it.

denali measured, on ONE screen (Replogle K562) against 50 Hallmark programs, that
set size alone explains 46.5% of apparent reversibility. The obvious question a
reviewer asks is whether that generalises. BioGRID ORCS 2.0.18 ships 1,952 curated
human screens from 418 publications, each with an explicit HIT=YES/NO column -- so
each screen can be reduced to exactly the set/size/hits table the audit consumes,
and the audit can run on the field as actually practised.

THE ESTIMANDS ARE NOT THE SAME AND MUST NOT BE CONFLATED.
  denali: R^2 of log10(1+n_hits) on RAW n_present, over 50 Hallmark programs,
          within one deeply-sampled genome-scale Perturb-seq screen.
  here:   per screen, R^2 of log10(1+hits-per-set) on LOG10(set-size) across the
          Hallmark sets, then the DISTRIBUTION of that R^2 over ~1,300 published
          screens of wildly varying design, library, phenotype and threshold.
Note the predictor transform differs from src/audit_screen.py (log size here,
raw size there). Both are computed below; the headline uses log size, and the
raw-size median is reported alongside so nobody has to trust the choice.
A smaller number here does not falsify denali's; it bounds how far it travels.

    python -m src.corpus_audit

Reads data/raw/orcs/ (see docs/CORPUS.md for the download and its HTTP/1.1
gotcha) and data/genesets/h.all.v2026.1.Hs.symbols.gmt.
Writes results/corpus/corpus_audit.json and results/corpus/corpus_per_screen.csv.
Names no screen, no publication and no gene set as a finding: the unit of
inference is the distribution.
"""
from __future__ import annotations

import glob
import json
from pathlib import Path

import numpy as np
import pandas as pd

GMT = Path("data/genesets/h.all.v2026.1.Hs.symbols.gmt")
RAW = Path("data/raw/orcs")
OUTDIR = Path("results/corpus")


def load_gmt(path: Path) -> dict[str, set[str]]:
    sets = {}
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        f = line.split("\t")
        sets[f[0]] = set(f[2:])
    return sets


def r2(x, y) -> float:
    x, y = np.asarray(x, float), np.asarray(y, float)
    if len(x) < 8 or np.allclose(y, y[0]) or np.allclose(x, x[0]):
        return float("nan")
    X = np.column_stack([np.ones(len(x)), x])
    b, *_ = np.linalg.lstsq(X, y, rcond=None)
    p = X @ b
    return float(1 - ((y - p) ** 2).sum() / ((y - y.mean()) ** 2).sum())


def main() -> int:
    sets = load_gmt(GMT)
    print(f"{len(sets)} Hallmark sets loaded")

    idx_path = glob.glob(str(RAW / "*index.tab.txt"))[0]
    idx = pd.read_csv(idx_path, sep="\t", low_memory=False)
    idx.columns = [c.lstrip("#") for c in idx.columns]
    idx["SCREEN_ID"] = idx["SCREEN_ID"].astype(str)
    meta = idx.set_index("SCREEN_ID")
    print(f"index: {len(idx)} screens")

    rows = []
    # No silent caps: every screen file is accounted for in exactly one bucket.
    n_parse_failed = n_excluded = 0
    files = sorted(glob.glob(str(RAW / "*screen.tab.txt")))
    for i, f in enumerate(files):
        if i % 400 == 0:
            print(f"  {i}/{len(files)}")
        try:
            d = pd.read_csv(f, sep="\t", usecols=["#SCREEN_ID", "OFFICIAL_SYMBOL", "HIT"],
                            low_memory=False)
        except Exception:
            n_parse_failed += 1
            continue
        sid = str(d["#SCREEN_ID"].iloc[0]) if len(d) else None
        if sid is None:
            n_parse_failed += 1
            continue
        hits = set(d.loc[d.HIT.astype(str).str.upper() == "YES", "OFFICIAL_SYMBOL"].dropna())
        measured = set(d.OFFICIAL_SYMBOL.dropna())
        if len(hits) < 20 or len(measured) < 10000:
            n_excluded += 1
            continue
        # per-set: size = members MEASURED in this screen; hits = members that were hits
        size, nhit = [], []
        for g in sets.values():
            m = g & measured
            if len(m) < 5:
                continue
            size.append(len(m))
            nhit.append(len(g & hits))
        if len(size) < 8:
            n_excluded += 1
            continue
        v = r2(np.log10(np.array(size)), np.log10(1 + np.array(nhit)))
        v_raw = r2(np.array(size), np.log10(1 + np.array(nhit)))
        if not np.isfinite(v):
            n_excluded += 1
            continue
        m = meta.loc[sid] if sid in meta.index else None
        rows.append({
            "screen_id": sid,
            "r2_size_alone": round(v, 4),
            "r2_size_raw": round(v_raw, 4) if np.isfinite(v_raw) else np.nan,
            "n_hits": len(hits),
            "n_measured": len(measured),
            "n_sets_used": len(size),
            "source_id": str(m["SOURCE_ID"]) if m is not None else "",
            "cell_line": str(m["CELL_LINE"]) if m is not None else "",
            "phenotype": str(m["PHENOTYPE"]) if m is not None else "",
            "library": str(m["LIBRARY"]) if m is not None else "",
        })

    R = pd.DataFrame(rows)
    print(f"\nfiles: {len(files)}  parse-failed: {n_parse_failed}  "
          f"excluded by rule: {n_excluded}  audited: {len(R)}")
    q = R.r2_size_alone.quantile([0.10, 0.25, 0.50, 0.75, 0.90]).round(4)
    print("\nR^2 (size alone) across published screens:")
    for k, v in q.items():
        print(f"  p{int(k*100):02d}  {v:.4f}")
    print(f"  mean {R.r2_size_alone.mean():.4f}")
    print(f"\nshare of screens above denali's 0.465: "
          f"{100*(R.r2_size_alone >= 0.465).mean():.1f}%")
    print(f"share above 0.25: {100*(R.r2_size_alone >= 0.25).mean():.1f}%")
    print(f"robustness: median R^2 with RAW size predictor (audit_screen's "
          f"transform): {R.r2_size_raw.median():.4f}")

    print("\nstratified by hit-list size:")
    bins = [(20, 100), (100, 500), (500, 2000), (2000, 10**9)]
    strat = []
    for lo, hi in bins:
        s = R[(R.n_hits >= lo) & (R.n_hits < hi)]
        if len(s) < 5:
            continue
        strat.append({"bin": f"{lo}-{hi if hi < 10**9 else 'inf'}", "n": len(s),
                      "median_r2": round(float(s.r2_size_alone.median()), 4)})
        print(f"  {strat[-1]['bin']:>12s}  n={len(s):4d}  median R2 = {strat[-1]['median_r2']:.4f}")

    report = {
        "status": "POST-HOC, exploratory. Not pre-registered.",
        "estimand_warning": "Not the same quantity as denali's 0.465 (one screen, "
                            "Perturb-seq, program-level R_p, raw-size predictor). "
                            "This is the distribution of a per-screen size-only R^2 "
                            "(log-size predictor) across published screens.",
        "source": "BioGRID ORCS 2.0.18, human, MIT licence. 1,952 screens / 418 publications.",
        "gene_sets": "MSigDB Hallmark v2026.1.Hs, 50 sets",
        "inclusion": "HIT=YES count >= 20 and >= 10,000 genes measured; >= 8 usable sets "
                     "(a set is usable with >= 5 measured members)",
        "n_screen_files": int(len(files)),
        "n_parse_failed": int(n_parse_failed),
        "n_excluded_by_rule": int(n_excluded),
        "n_screens_audited": int(len(R)),
        "quantiles": {f"p{int(k*100)}": float(v) for k, v in q.items()},
        "mean": round(float(R.r2_size_alone.mean()), 4),
        "pct_at_or_above_denali_0465": round(100 * float((R.r2_size_alone >= 0.465).mean()), 1),
        "pct_at_or_above_025": round(100 * float((R.r2_size_alone >= 0.25).mean()), 1),
        "median_r2_raw_size_predictor": round(float(R.r2_size_raw.median()), 4),
        "stratified_by_hitlist_size": strat,
    }
    OUTDIR.mkdir(parents=True, exist_ok=True)
    (OUTDIR / "corpus_audit.json").write_text(json.dumps(report, indent=2) + "\n")
    R.to_csv(OUTDIR / "corpus_per_screen.csv", index=False)
    print(f"\nwrote {OUTDIR}/corpus_audit.json and {OUTDIR}/corpus_per_screen.csv")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
