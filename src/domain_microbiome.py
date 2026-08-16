"""Domain 5 — microbiome functions. The multi-cohort domain.

Pre-registered in docs/DOMAINS_PREREG.md (6d40a079..., a2776f7). CORRECTION 1
(commit 8d2296a), fixed BEFORE any domain-5 value was computed, replaces the
registered set definition: the MetaCyc superpathway/ontology-class hierarchy
is not publicly obtainable, so sets are MetaCyc pathways and members are the
species carrying them, read from the stratified HUMAnN table that
curatedMetagenomicData already ships. THIS IS A DEVIATION AND IS LABELLED AS
ONE WHEREVER IT IS REPORTED.

Substrate: curatedMetagenomicData 3.20.0, every stool CRC/control cohort with
n >= 20 per group (11 cohorts), pathway abundance, written by
src/microbiome_extract.R.

Construction:
  hit rule   Welch t on log10 relative abundance, CRC vs control, BH q < 0.05
             WITHIN cohort, applied to species-stratified pathway rows
  sets       MetaCyc pathways; members = species strata measured for that
             pathway in that cohort; usable at >= 5 measured member strata
  unit       the cohort. Every statistic is computed per cohort and the
             DISTRIBUTION over cohorts is reported, never a single cohort.

Because there are 11 cohorts this domain also carries the concordance arm:
when two independent cohorts agree on a pathway ranking, how much of the
agreement is set size? That is `audit_replication` verbatim, run over all 55
cohort pairs.

Writes results/domains/microbiome.json. Names no cohort, pathway or species.

    .venv/bin/python -m src.domain_microbiome
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import ttest_ind

sys.path.insert(0, str(Path("packages/denali-audit").resolve()))
from denali_audit.core import audit, audit_replication, rerank  # noqa: E402

BASE = Path("data/raw/microbiome")
CORPUS = Path("results/corpus/corpus_per_screen.csv")
OUT = Path("results/domains/microbiome.json")

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


def one_cohort(name: str):
    m = pd.read_csv(BASE / f"{name}_pathways.tsv", sep="\t", index_col=0)
    md = pd.read_csv(BASE / f"{name}_meta.tsv", sep="\t")
    cond = md.set_index("sample").condition.reindex(m.columns)
    strat = [i for i in m.index if "|" in str(i)]
    m = m.loc[strat]
    if not len(m):
        return None
    is_crc = (cond == "CRC").values
    X = np.log10(m.values.astype(float) + 1e-6)
    keep = (np.isfinite(X).all(1)) & (X.std(1) > 0)
    m, X = m.loc[keep], X[keep]
    if len(m) < 50:
        return None
    res = ttest_ind(X[:, is_crc], X[:, ~is_crc], axis=1, equal_var=False)
    p = np.asarray(res.pvalue, float)
    ok = np.isfinite(p)
    rows = np.array(m.index)[ok]
    q = bh(p[ok])
    hit = q < Q

    members = defaultdict(list)
    for r, h in zip(rows, hit):
        pw = str(r).split("|")[0]
        members[pw].append(bool(h))
    names, size, nhit = [], [], []
    for pw, hs in members.items():
        if len(hs) >= MIN_MEMBERS:
            names.append(pw)
            size.append(len(hs))
            nhit.append(int(sum(hs)))
    if len(size) < 8:
        return None
    return {
        "cohort": name, "n_samples": int(m.shape[1]),
        "n_crc": int(is_crc.sum()), "n_strata": int(len(rows)),
        "hit_fraction": float(hit.mean()),
        "names": names, "size": size, "hits": nhit,
    }


def main() -> int:
    cohorts = sorted(p.name.replace("_pathways.tsv", "")
                     for p in BASE.glob("*_pathways.tsv"))
    print(f"{len(cohorts)} cohorts on disk")
    data = [d for d in (one_cohort(c) for c in cohorts) if d]
    print(f"{len(data)} cohorts usable")
    if len(data) < 2:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps({"domain": "microbiome functions",
                                   "status": "no defensible number here",
                                   "reason": f"{len(data)} usable cohorts"},
                                  indent=2) + "\n")
        return 0

    corpus = pd.read_csv(CORPUS).r2_size_alone.dropna()
    per = []
    for d in data:
        A = audit(d["size"], d["hits"])
        rr = rerank(d["size"], d["hits"], names=d["names"], top=10)
        lg = r2_log(d["size"], d["hits"])
        # A cohort in which no member stratum is significant leaves the outcome
        # constant, and the R^2 of a constant is undefined -- not zero, and
        # certainly not "not size-dominated". Those cohorts are UNSCOREABLE and
        # are counted, never scored. This is the statistic's own domain, not a
        # threshold chosen after seeing the data.
        scoreable = bool(np.isfinite(A["r2_size_alone"]) and np.isfinite(lg))
        per.append({
            "n_sets": A["n_sets"], "size_range": A["size_range"],
            "median_set_size": int(np.median(d["size"])),
            "hit_fraction": round(d["hit_fraction"], 5),
            "n_member_strata_significant": int(sum(d["hits"])),
            "scoreable": scoreable,
            "r2_size_alone_raw": A["r2_size_alone"] if scoreable else None,
            "r2_size_alone_log": round(lg, 4) if scoreable else None,
            "verdict": A["verdict"] if scoreable else
                       "UNSCOREABLE — no member stratum is significant, so the "
                       "outcome is constant and the statistic is undefined",
            "corpus_percentile_logsize": (
                round(float((corpus < lg).mean() * 100), 1) if scoreable else None),
            "rerank_top10_survived": rr["survived_top_n"] if scoreable else None,
        })
    good = [p for p in per if p["scoreable"]]
    if len(good) < 2:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(
            {"domain": "microbiome functions",
             "status": "no defensible number here",
             "reason": f"only {len(good)} of {len(per)} cohorts are scoreable; "
                       f"the rest return no significant member stratum",
             "per_cohort": per}, indent=2) + "\n")
        print("no defensible number here")
        return 0
    raw = np.array([p["r2_size_alone_raw"] for p in good], float)
    lgs = np.array([p["r2_size_alone_log"] for p in good], float)
    surv = np.array([p["rerank_top10_survived"] for p in good], float)

    # ---- concordance arm: how much of cross-cohort agreement is set size?
    pairs = []
    idx_good = [i for i, p in enumerate(per) if p["scoreable"]]
    n_possible = len(idx_good) * (len(idx_good) - 1) // 2
    for i, j in combinations(idx_good, 2):
        a, b = data[i], data[j]
        common = sorted(set(a["names"]) & set(b["names"]))
        if len(common) < 8:
            continue
        ai = {n: (s, h) for n, s, h in zip(a["names"], a["size"], a["hits"])}
        bi = {n: (s, h) for n, s, h in zip(b["names"], b["size"], b["hits"])}
        sz = [(ai[n][0] + bi[n][0]) / 2 for n in common]
        try:
            r = audit_replication(sz, [ai[n][1] for n in common],
                                  [bi[n][1] for n in common])
        except Exception:
            continue
        if np.isfinite(r["pct_of_agreement_that_is_size"]):
            pairs.append(r)
    share = np.array([p["pct_of_agreement_that_is_size"] for p in pairs], float)
    rawa = np.array([p["agreement_raw"] for p in pairs], float)

    report = {
        "domain": "microbiome functions",
        "status": "Pre-registered in docs/DOMAINS_PREREG.md (6d40a079..., a2776f7).",
        "DEVIATION": {
            "what": "Set definition replaced by CORRECTION 1 (commit 8d2296a), "
                    "fixed before any domain-5 value was computed.",
            "registered": "sets = MetaCyc superpathway/ontology-class groupings",
            "used": "sets = MetaCyc pathways, members = species carrying them",
            "why": "The MetaCyc class hierarchy is not publicly obtainable; "
                   "HUMAnN's public structured file expands superpathways to "
                   "reactions and MetaCyc's own hierarchy is license-gated.",
        },
        "substrate": "curatedMetagenomicData 3.20.0, stool CRC vs control, "
                     "n >= 20 per group per cohort",
        "construction": {
            "hit_rule": f"Welch t on log10 relative abundance, BH q < {Q} within cohort",
            "usable_set_floor": MIN_MEMBERS,
            "unit_of_inference": "the cohort; the distribution over cohorts is "
                                 "reported, never a single cohort",
        },
        "n_cohorts": len(data),
        "n_cohorts_scoreable": len(good),
        "power_note": {
            "unscoreable": len(per) - len(good),
            "why": "The registered hit rule (BH q < 0.05 within cohort) returns "
                   "NO significant member stratum in these cohorts, so the "
                   "outcome is constant and a size-alone R^2 does not exist. "
                   "They are counted, not scored, and they are not evidence "
                   "that the confound is absent -- they are evidence that the "
                   "cohort cannot answer the question. Reporting them as "
                   "'not size-dominated' would have been the error this "
                   "project exists to catch.",
        },
        "across_cohorts": {
            "n": len(good),
            "r2_size_alone_raw_median": round(float(np.median(raw)), 4),
            "r2_size_alone_raw_range": [round(float(raw.min()), 4),
                                        round(float(raw.max()), 4)],
            "r2_size_alone_log_median": round(float(np.median(lgs)), 4),
            "corpus_percentile_logsize_median": round(float(np.median(
                [p["corpus_percentile_logsize"] for p in good])), 1),
            "verdicts": {v: int(sum(1 for p in good if p["verdict"] == v))
                         for v in {p["verdict"] for p in good}},
            "rerank_top10_survived_median": float(np.median(surv)),
            "median_set_size_median": int(np.median(
                [p["median_set_size"] for p in good])),
            "size_range_widest": [int(min(p["size_range"][0] for p in good)),
                                  int(max(p["size_range"][1] for p in good))],
        },
        "concordance_arm": ({
            "what": "audit_replication verbatim over every cohort pair: when "
                    "two independent cohorts agree on a pathway ranking, how "
                    "much of the agreement is set size?",
            "n_pairs": len(pairs),
            "n_pairs_possible_among_scoreable": n_possible,
            "agreement_raw_median": round(float(np.median(rawa)), 4),
            "pct_of_agreement_that_is_size_median": round(float(np.median(share)), 1),
            "pct_q25_q75": [round(float(np.quantile(share, 0.25)), 1),
                            round(float(np.quantile(share, 0.75)), 1)],
        } if pairs else {"status": "no defensible number here — no usable pairs"}),
        "per_cohort": per,
        "scope": "No cohort, pathway or species is named as a finding.",
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report["across_cohorts"], indent=2))
    print(json.dumps(report["concordance_arm"], indent=2))
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
