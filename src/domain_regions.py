"""Domain 2 — region sets. Genomic intervals, no gene identifiers anywhere.

Pre-registered in docs/DOMAINS_PREREG.md (6d40a079..., commit a2776f7).

This domain matters because it shares NOTHING with the gene-set machinery: no
gene symbols, no annotation database, no curation. A "set" is a pile of
genomic intervals produced by an experiment, and its "size" is how many peaks
that experiment called -- which is a property of antibody, depth and peak
caller, not of biology. If the confound is arithmetic it must appear here.

Substrate, both public, no auth:
  NHGRI-EBI GWAS Catalog associations (GRCh38 coordinates, as ChIP-Atlas hg38)
  ChIP-Atlas per-experiment peak calls, hg38, q < 1e-05 (bed05)

Construction, from the pre-registration:
  query      genome-wide significant SNPs (p < 5e-8) for the MAPPED_TRAIT with
             the most such associations -- a deterministic, capability-blind
             rule fixed before the catalogue was read
  sets       ChIP-Atlas experiments; size = peaks called in that experiment;
             hits = query SNPs falling inside at least one of its peaks

IMPLEMENTATION DECISIONS, fixed before any value was computed (the
pre-registration named the sources but not the experiment subset):
  - assembly hg38, antigen class "TFs and others", cell-type class = the class
    with the most such experiments. Chosen by the same "most" rule as the
    trait, so neither is picked to suit the other.
  - experiments sorted by ID ascending, first 300 taken. NO SILENT CAPS: the
    number available and the number dropped are both reported.
  - set size is COUNTED FROM THE DOWNLOADED PEAK FILE, not taken from the
    metadata column, and the two are cross-checked; the agreement rate is
    reported rather than assumed.

The trait and the cell-type class are selected independently, so this is not
a tissue-matched analysis and nothing here is a biological claim about either.

Writes results/domains/regions.json. Names no experiment, antigen or trait as
a finding beyond the deterministic selection rule.

    .venv/bin/python -m src.domain_regions
"""
from __future__ import annotations

import json
import sys
from bisect import bisect_right
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path("packages/denali-audit").resolve()))
from denali_audit.core import audit, rerank  # noqa: E402

BASE = Path("data/raw/regions")
GWAS = BASE / "gwas-catalog-download-associations-alt-full.tsv"
SELECTED = BASE / "blood_tf_selected.tsv"
ALL_AVAIL = BASE / "blood_tf_all.tsv"
BED = BASE / "bed"
CORPUS = Path("results/corpus/corpus_per_screen.csv")
OUT = Path("results/domains/regions.json")

P_CUT = 5e-8
MIN_MEMBERS = 5


def query_snps() -> tuple[str, dict[str, list[int]], int]:
    d = pd.read_csv(GWAS, sep="\t", dtype=str, low_memory=False)
    d["p"] = pd.to_numeric(d["P-VALUE"], errors="coerce")
    g = d[(d.p < P_CUT) & d.CHR_ID.notna() & d.CHR_POS.notna()
          & d.MAPPED_TRAIT.notna()]
    trait = g.MAPPED_TRAIT.value_counts().index[0]
    s = g[g.MAPPED_TRAIT == trait]
    pos = set()
    for c, p in zip(s.CHR_ID, s.CHR_POS):
        for cc, pp in zip(str(c).split(";"), str(p).split(";")):
            cc, pp = cc.strip(), pp.strip()
            if cc and pp.isdigit():
                pos.add((f"chr{cc}", int(pp)))
    by_chr = defaultdict(list)
    for c, p in pos:
        by_chr[c].append(p)
    return trait, {c: sorted(v) for c, v in by_chr.items()}, len(pos)


def overlap_count(bed: Path, snps: dict[str, list[int]]) -> tuple[int, int]:
    """(peaks in file, query SNPs falling inside at least one peak)."""
    iv = defaultdict(list)
    n_peaks = 0
    with bed.open() as fh:
        for line in fh:
            if line.startswith(("track", "#", "browser")):
                continue
            f = line.split("\t")
            if len(f) < 3:
                continue
            try:
                iv[f[0]].append((int(f[1]), int(f[2])))
            except ValueError:
                continue
            n_peaks += 1
    hit = 0
    for c, pts in snps.items():
        segs = iv.get(c)
        if not segs:
            continue
        segs.sort()
        starts = [s for s, _ in segs]
        # running max end, so a point is inside some peak iff it is <= the max
        # end among peaks starting at or before it
        maxend, run = [], -1
        for _, e in segs:
            run = max(run, e)
            maxend.append(run)
        for p in pts:
            i = bisect_right(starts, p) - 1
            if i >= 0 and p < maxend[i]:
                hit += 1
    return n_peaks, hit


def r2_log(size, hits) -> float:
    s = np.log10(np.asarray(size, float))
    y = np.log10(1 + np.asarray(hits, float))
    if len(s) < 8 or np.std(s) == 0 or np.std(y) == 0:
        return float("nan")
    b = np.polyfit(s, y, 1)
    return float(1 - ((y - np.polyval(b, s)) ** 2).sum() / ((y - y.mean()) ** 2).sum())


def main() -> int:
    trait, snps, n_snp = query_snps()
    print(f"query trait (most genome-wide significant associations): {trait}")
    print(f"{n_snp} unique SNP positions")

    sel = pd.read_csv(SELECTED, sep="\t", header=None,
                      names=["srx", "meta_peaks", "antigen"], dtype=str)
    sel["meta_peaks"] = pd.to_numeric(sel.meta_peaks, errors="coerce")
    n_avail = sum(1 for _ in ALL_AVAIL.open())

    names, size, nhit, meta_ok, missing = [], [], [], 0, 0
    for i, r in enumerate(sel.itertuples()):
        if i % 50 == 0:
            print(f"  {i}/{len(sel)}")
        f = BED / f"{r.srx}.bed"
        if not f.exists() or f.stat().st_size == 0:
            missing += 1
            continue
        n_peaks, h = overlap_count(f, snps)
        if n_peaks < MIN_MEMBERS:
            continue
        if abs(n_peaks - r.meta_peaks) <= max(1, 0.02 * r.meta_peaks):
            meta_ok += 1
        names.append(r.srx)
        size.append(n_peaks)
        nhit.append(h)

    print(f"{len(size)} experiments audited, {missing} files missing, "
          f"metadata peak count agrees on {meta_ok}")
    if len(size) < 8:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps({"domain": "region sets",
                                   "status": "no defensible number here",
                                   "reason": f"only {len(size)} usable sets"},
                                  indent=2) + "\n")
        return 0

    A = audit(size, nhit)
    rr = rerank(size, nhit, names=names, top=10)
    lg = r2_log(size, nhit)
    corpus = pd.read_csv(CORPUS).r2_size_alone.dropna()

    report = {
        "domain": "region sets",
        "status": "Pre-registered in docs/DOMAINS_PREREG.md (6d40a079..., a2776f7).",
        "why_this_domain": "Shares no gene identifiers, no annotation database "
                           "and no curation with the gene-set machinery. A set "
                           "is a pile of intervals and its size is a property "
                           "of antibody, depth and peak caller.",
        "substrate": "NHGRI-EBI GWAS Catalog (GRCh38) x ChIP-Atlas hg38 peak "
                     "calls at q < 1e-05",
        "construction": {
            "query_trait": trait,
            "query_rule": "MAPPED_TRAIT with the most associations at "
                          f"p < {P_CUT:g}; deterministic and capability-blind",
            "n_query_snps": n_snp,
            "set_rule": "hg38 'TFs and others' experiments in the cell-type "
                        "class with the most such experiments, sorted by ID, "
                        "first 300",
            "n_experiments_available": n_avail,
            "n_experiments_selected": len(sel),
            "n_experiments_audited": len(size),
            "n_bed_files_missing": missing,
            "metadata_peak_count_agreement": f"{meta_ok}/{len(size)}",
            "tissue_matching": "NONE. Trait and cell-type class are selected by "
                               "independent rules; this is not a biological "
                               "claim about either.",
        },
        "n_sets": A["n_sets"],
        "size_range": A["size_range"],
        "median_set_size": int(np.median(size)),
        "size_fold_range": round(float(max(size) / max(1, min(size))), 1),
        "r2_size_alone_raw": A["r2_size_alone"],
        "r2_size_alone_log": round(lg, 4),
        "spearman_size_vs_hits": A["spearman_size_vs_hits"],
        "verdict": A["verdict"],
        "corpus_percentile_logsize": round(float((corpus < lg).mean() * 100), 1),
        "rerank_top10_survived": rr["survived_top_n"],
        "rerank_top10_left": rr["left_top_n"],
        "sets_with_zero_hits": A["sets_with_zero_hits"],
        "scope": "No experiment, antigen or publication is named as a finding.",
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: report[k] for k in
                      ("n_sets", "size_range", "size_fold_range",
                       "r2_size_alone_raw", "r2_size_alone_log", "verdict",
                       "corpus_percentile_logsize", "rerank_top10_survived")},
                     indent=2))
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
