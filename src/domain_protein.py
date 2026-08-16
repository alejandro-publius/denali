"""Domain 4 — protein sets. Reactome pathways against real tumour proteomics.

Pre-registered in docs/DOMAINS_PREREG.md (6d40a079..., commit a2776f7, before
any substrate was downloaded).

Substrate, all public, no auth:
  CPTAC COAD proteome (TMT, unshared log-ratio) tumour and normal matrices via
    LinkedOmics -- 8,067 gene-level protein quantifications
  Reactome UniProt2Reactome.txt, human -- the registered pathway definitions
  UniProt HUMAN_9606_idmapping.dat.gz -- to carry Reactome's UniProt
    accessions onto the matrix's gene symbols. The registered source is used
    as registered; this file only performs the identifier join, and the join
    rate is reported rather than assumed.

Construction, fixed in the pre-registration:
  per-protein  Welch t, tumour vs normal, BH q < 0.05 -> hit. If the hit
               fraction falls outside [1%, 60%] the top-10%-by-|t| variant is
               ALSO reported (this guard was registered in advance).
  sets         Reactome human pathways, size = measured mapped proteins,
               usable at >= 5 measured members

Writes results/domains/protein.json. Names no protein and no pathway.

    .venv/bin/python -m src.domain_protein
"""
from __future__ import annotations

import gzip
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import ttest_ind

sys.path.insert(0, str(Path("packages/denali-audit").resolve()))
from denali_audit.core import audit, rerank  # noqa: E402

BASE = Path("data/raw/protein")
TUMOR = BASE / "PNNL_Tumor_TMT_UnsharedLogRatio.cct"
NORMAL = BASE / "PNNL_Normal_TMT_UnsharedLogRatio.cct"
U2R = BASE / "UniProt2Reactome.txt"
IDMAP = BASE / "HUMAN_9606_idmapping.dat.gz"
CORPUS = Path("results/corpus/corpus_per_screen.csv")
OUT = Path("results/domains/protein.json")

Q = 0.05
MIN_MEMBERS = 5


def bh(p):
    p = np.asarray(p, float)
    n = len(p)
    o = np.argsort(p)
    q = np.empty(n)
    q[o] = np.minimum.accumulate((p[o] * n / np.arange(1, n + 1))[::-1])[::-1]
    return np.minimum(q, 1.0)


def r2_log(size, hits) -> float:
    s = np.log10(np.asarray(size, float))
    y = np.log10(1 + np.asarray(hits, float))
    if len(s) < 8 or np.std(s) == 0 or np.std(y) == 0:
        return float("nan")
    b = np.polyfit(s, y, 1)
    return float(1 - ((y - np.polyval(b, s)) ** 2).sum() / ((y - y.mean()) ** 2).sum())


def build(sets, measured, hits, floor=MIN_MEMBERS):
    names, size, nhit = [], [], []
    for n, mem in sets.items():
        mm = mem & measured
        if len(mm) >= floor:
            names.append(n)
            size.append(len(mm))
            nhit.append(len(mm & hits))
    return names, size, nhit


def summarise(names, size, nhit, corpus, label=None):
    A = audit(size, nhit)
    rr = rerank(size, nhit, names=names, top=10)
    lg = r2_log(size, nhit)
    out = {
        "n_sets": A["n_sets"],
        "size_range": A["size_range"],
        "median_set_size": int(np.median(size)),
        "r2_size_alone_raw": A["r2_size_alone"],
        "r2_size_alone_log": round(lg, 4),
        "spearman_size_vs_hits": A["spearman_size_vs_hits"],
        "verdict": A["verdict"],
        "corpus_percentile_logsize": round(float((corpus < lg).mean() * 100), 1),
        "rerank_top10_survived": rr["survived_top_n"],
        "rerank_top10_left": rr["left_top_n"],
        "sets_with_zero_hits": A["sets_with_zero_hits"],
    }
    if label:
        out["label"] = label
    return out


def main() -> int:
    t = pd.read_csv(TUMOR, sep="\t", index_col=0)
    n = pd.read_csv(NORMAL, sep="\t", index_col=0)
    common = t.index.intersection(n.index)
    t, n = t.loc[common], n.loc[common]
    print(f"CPTAC COAD: {len(common)} proteins, {t.shape[1]} tumour / "
          f"{n.shape[1]} normal samples")

    tv, nv = t.values.astype(float), n.values.astype(float)
    keep = (np.isfinite(tv).sum(1) >= 10) & (np.isfinite(nv).sum(1) >= 10)
    genes = np.array(common)[keep]
    res = ttest_ind(tv[keep], nv[keep], axis=1, equal_var=False,
                    nan_policy="omit")
    p = np.asarray(res.pvalue, float)
    tstat = np.asarray(res.statistic, float)
    ok = np.isfinite(p)
    genes, p, tstat = genes[ok], p[ok], tstat[ok]
    q = bh(p)
    hits = set(genes[q < Q])
    measured = set(genes)
    hit_frac = len(hits) / len(measured)
    print(f"{len(measured)} testable proteins, {len(hits)} hits at BH q<{Q} "
          f"({hit_frac:.1%})")

    # Reactome, as registered, joined onto symbols via UniProt
    acc2sym = {}
    with gzip.open(IDMAP, "rt") as fh:
        for line in fh:
            f = line.rstrip("\n").split("\t")
            if len(f) == 3 and f[1] == "Gene_Name":
                acc2sym.setdefault(f[0], f[2])
    print(f"{len(acc2sym)} UniProt accessions carry a gene symbol")

    sets = defaultdict(set)
    n_acc = n_mapped = 0
    with U2R.open() as fh:
        for line in fh:
            f = line.rstrip("\n").split("\t")
            if len(f) < 6 or f[5] != "Homo sapiens":
                continue
            n_acc += 1
            s = acc2sym.get(f[0].split("-")[0])
            if s:
                n_mapped += 1
                sets[f[3]].add(s)
    join_rate = n_mapped / n_acc if n_acc else 0.0
    print(f"Reactome human rows {n_acc}, joined to a symbol {join_rate:.1%}, "
          f"{len(sets)} pathways")

    corpus = pd.read_csv(CORPUS).r2_size_alone.dropna()
    names, size, nhit = build(sets, measured, hits)
    if len(size) < 8:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps({"domain": "protein sets",
                                   "status": "no defensible number here",
                                   "reason": f"only {len(size)} usable sets"},
                                  indent=2) + "\n")
        return 0
    primary = summarise(names, size, nhit, corpus)

    # Registered guard: hit fraction outside [1%, 60%] -> also report top-10% by |t|
    guard_fired = not (0.01 <= hit_frac <= 0.60)
    variant = None
    if guard_fired:
        k = max(1, int(round(0.10 * len(measured))))
        strict = set(genes[np.argsort(-np.abs(tstat))[:k]])
        vn, vs, vh = build(sets, measured, strict)
        if len(vs) >= 8:
            variant = summarise(vn, vs, vh, corpus,
                                label="Registered variant, fired by the "
                                      "pre-registered hit-fraction guard: "
                                      f"top 10% by |t| ({k} proteins)")

    report = {
        "domain": "protein sets",
        "status": "Pre-registered in docs/DOMAINS_PREREG.md (6d40a079..., a2776f7).",
        "substrate": "CPTAC COAD proteome (LinkedOmics) x Reactome human pathways",
        "construction": {
            "hit_rule": f"Welch t tumour vs normal, BH q < {Q}",
            "n_proteins_testable": len(measured),
            "n_proteins_hit": len(hits),
            "hit_fraction": round(hit_frac, 4),
            "usable_set_floor": MIN_MEMBERS,
            "reactome_uniprot_to_symbol_join_rate": round(join_rate, 4),
        },
        "primary": primary,
        "hit_fraction_guard": {
            "registered_range": [0.01, 0.60],
            "fired": bool(guard_fired),
            "note": "The guard was registered in advance precisely so a "
                    "runaway hit rate could not be reported as a confound.",
        },
        "registered_variant_top10pct_by_t": variant or {
            "status": "not required — hit fraction inside the registered range"},
        "scope": "No protein and no pathway is named as a finding.",
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(primary, indent=2))
    if variant:
        print("variant:", json.dumps({k: variant[k] for k in
                                      ("r2_size_alone_raw", "r2_size_alone_log",
                                       "verdict", "corpus_percentile_logsize")}))
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
