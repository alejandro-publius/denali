"""Domain 6 — yeast genetic interaction. The best-annotated organism in biology.

Pre-registered in docs/DOMAINS_PREREG.md (sha256 6d40a079..., commit a2776f7,
BEFORE any substrate was downloaded). This domain runs first because it kills
the strongest objection to the whole project: if the size confound holds in
S. cerevisiae — where the GO annotation is decades deep and curator-reviewed —
it cannot be blamed on sloppy human curation.

Substrate, both single GETs, no auth:
  Costanzo et al. 2016 Science 353:aaf1420, Data File S1 (pair-wise format),
    SGA_NxN / SGA_ExN / SGA_ExE — the global genetic interaction network
  SGD go_slim_mapping.tab — curated GO Slim, the annotation a yeast biologist
    would actually use for enrichment

Construction, fixed in the pre-registration:
  gene statistic : number of significant NEGATIVE genetic interactions, at the
                   study's published intermediate stringency (p < 0.05 and
                   |eps| > 0.08, negative sign)
  hit rule       : top 10% of measured genes by that count
                   (registered sensitivities: 5% and 20%)
  sets           : GO Slim biological process (registered sensitivities:
                   component, function), size = annotated genes among measured
  usable set     : >= 5 measured members (the tool's own floor)

Then the identical recipe every domain gets: core.audit raw-size R^2 with its
verdict, the log-size variant for percentile placement against the committed
1,272-screen CRISPR corpus, and core.rerank top-10 survival.

Writes results/domains/yeast.json. Names no gene and no GO term as a finding.

    .venv/bin/python -m src.domain_yeast
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path("packages/denali-audit").resolve()))
from denali_audit.core import audit, rerank  # noqa: E402

BASE = Path("data/raw/yeast")
SGA = BASE / "Data File S1. Raw genetic interaction datasets: Pair-wise interaction format"
FILES = ["SGA_NxN.txt", "SGA_ExN.txt", "SGA_ExE.txt"]
GOSLIM = BASE / "go_slim_mapping.tab"
CORPUS = Path("results/corpus/corpus_per_screen.csv")
OUT = Path("results/domains/yeast.json")

EPS_CUT = 0.08          # Costanzo intermediate stringency
P_CUT = 0.05
QUANTILES = {"primary_top10": 0.10, "sens_top05": 0.05, "sens_top20": 0.20}
NAMESPACE = {"primary_P": "P", "sens_C": "C", "sens_F": "F"}


def orf(strain_id: str) -> str:
    return strain_id.split("_", 1)[0].strip().upper()


def scan() -> tuple[dict, dict]:
    """Stream the SGA files; per ORF: opportunities tested, negative hits."""
    tested = defaultdict(int)
    neg = defaultdict(int)
    for fname in FILES:
        path = SGA / fname
        if not path.exists():
            print(f"  MISSING {fname}")
            continue
        n = 0
        for chunk in pd.read_csv(path, sep="\t", usecols=[0, 2, 5, 6],
                                 names=["q", "a", "eps", "p"], header=0,
                                 chunksize=2_000_000, low_memory=False):
            eps = pd.to_numeric(chunk.eps, errors="coerce")
            pv = pd.to_numeric(chunk.p, errors="coerce")
            q = chunk.q.map(orf)
            a = chunk.a.map(orf)
            ok = eps.notna() & pv.notna()
            for s in (q[ok], a[ok]):
                for g, c in s.value_counts().items():
                    tested[g] += int(c)
            sig = ok & (pv < P_CUT) & (eps < -EPS_CUT)
            for s in (q[sig], a[sig]):
                for g, c in s.value_counts().items():
                    neg[g] += int(c)
            n += len(chunk)
        print(f"  {fname}: {n:,} pairs")
    return dict(tested), dict(neg)


def load_goslim(measured: set[str]) -> dict[str, dict[str, set[str]]]:
    cols = ["orf", "gene", "sgdid", "aspect", "term", "goid", "feature"]
    g = pd.read_csv(GOSLIM, sep="\t", names=cols, dtype=str, low_memory=False)
    g = g.dropna(subset=["orf", "aspect", "term"])
    g["orf"] = g.orf.str.upper()
    g = g[g.orf.isin(measured)]
    out = {}
    for asp in set(NAMESPACE.values()):
        sub = g[g.aspect == asp]
        d = defaultdict(set)
        for term, o in zip(sub.term, sub.orf):
            if term.lower() not in ("other", "not_yet_annotated"):
                d[term].add(o)
        out[asp] = dict(d)
    return out


def build(sets: dict[str, set[str]], measured: set[str],
          hits: set[str]) -> tuple[list, list, list]:
    names, size, nhit = [], [], []
    for name, members in sets.items():
        mem = members & measured
        if len(mem) < 5:
            continue
        names.append(name)
        size.append(len(mem))
        nhit.append(len(mem & hits))
    return names, size, nhit


def r2_log(size, hits) -> float:
    s = np.log10(np.asarray(size, float))
    y = np.log10(1 + np.asarray(hits, float))
    if len(s) < 8 or np.std(s) == 0 or np.std(y) == 0:
        return float("nan")
    b = np.polyfit(s, y, 1)
    return float(1 - ((y - np.polyval(b, s)) ** 2).sum() / ((y - y.mean()) ** 2).sum())


def main() -> int:
    print("streaming the global genetic interaction network")
    tested, neg = scan()
    measured = {g for g, t in tested.items() if t >= 100}   # tested at scale
    print(f"  {len(tested):,} ORFs seen, {len(measured):,} tested >= 100 times")
    degree = pd.Series({g: neg.get(g, 0) for g in measured}, dtype=float)

    slim = load_goslim(measured)
    print({a: len(s) for a, s in slim.items()})

    variants = {}
    for qname, q in QUANTILES.items():
        cut = degree.quantile(1 - q)
        hits = set(degree[degree > cut].index)
        for sname, asp in NAMESPACE.items():
            if qname != "primary_top10" and sname != "primary_P":
                continue                      # one axis at a time
            names, size, nhit = build(slim[asp], measured, hits)
            if len(size) < 8:
                variants[f"{qname}|{sname}"] = {"status": "no defensible number here",
                                                "reason": f"only {len(size)} usable sets"}
                continue
            a = audit(size, nhit)
            rr = rerank(size, nhit, names=names, top=10)
            variants[f"{qname}|{sname}"] = {
                "n_sets": a["n_sets"],
                "size_range": a["size_range"],
                "n_hit_genes": len(hits),
                "r2_size_alone_raw": a["r2_size_alone"],
                "r2_size_alone_log": round(r2_log(size, nhit), 4),
                "spearman_size_vs_hits": a["spearman_size_vs_hits"],
                "verdict": a["verdict"],
                "rerank_top10_survived": rr["survived_top_n"],
                "rerank_top10_left": rr["left_top_n"],
            }
    prim = variants["primary_top10|primary_P"]

    corpus = pd.read_csv(CORPUS).r2_size_alone.dropna()
    pct = float((corpus < prim["r2_size_alone_log"]).mean() * 100)

    # POST-HOC, labelled: degree normalised by opportunities tested. Not
    # registered; reported because the registered count statistic inherits the
    # study's own unequal query/array testing depth.
    opp = pd.Series({g: tested[g] for g in measured}, dtype=float)
    rate = degree / opp
    rate_hits = set(rate[rate > rate.quantile(0.90)].index)
    rn, rs, rh = build(slim["P"], measured, rate_hits)
    posthoc = audit(rs, rh) if len(rs) >= 8 else None

    report = {
        "domain": "yeast genetic interaction",
        "status": "Pre-registered in docs/DOMAINS_PREREG.md (6d40a079..., a2776f7).",
        "why_this_domain": "Best-annotated organism in biology. If the confound "
                           "holds here it cannot be blamed on sloppy curation.",
        "substrate": "Costanzo et al. 2016 Science 353:aaf1420 Data File S1 "
                     "(SGA_NxN + SGA_ExN + SGA_ExE) x SGD GO Slim",
        "construction": {
            "gene_statistic": "count of significant negative genetic interactions",
            "stringency": f"p < {P_CUT} and eps < -{EPS_CUT} (Costanzo intermediate)",
            "hit_rule": "top 10% of measured genes by that count",
            "measured_gene_rule": "ORF tested in >= 100 pairs",
            "sets": "GO Slim biological process, >= 5 measured members",
        },
        "n_genes_measured": int(len(measured)),
        "primary": prim,
        "corpus_percentile_logsize": round(pct, 1),
        "prereg_expectation": "log-size R^2 at or above the corpus 25th percentile "
                              "(0.186); below the 10th (0.103) would mean annotation "
                              "quality rescues set-level inference",
        "variants": variants,
        "post_hoc_rate_normalised": ({
            "note": "POST-HOC, not pre-registered. Hits = top 10% by negative "
                    "interactions PER PAIR TESTED, removing the study's unequal "
                    "query/array testing depth.",
            "r2_size_alone_raw": posthoc["r2_size_alone"],
            "r2_size_alone_log": round(r2_log(rs, rh), 4),
            "verdict": posthoc["verdict"],
        } if posthoc else {"status": "no defensible number here"}),
        "scope": "No gene and no GO term is named as a finding. The unit of "
                 "inference is the distribution over sets.",
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: prim[k] for k in
                      ("n_sets", "r2_size_alone_raw", "r2_size_alone_log",
                       "verdict", "rerank_top10_survived")}, indent=2))
    print(f"corpus percentile (log-size): {pct:.1f}")
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
