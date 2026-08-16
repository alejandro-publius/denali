"""Domain 3 — metabolite sets. The BOUNDARY CONDITION: does the confound
survive when sets are tiny?

Pre-registered in docs/DOMAINS_PREREG.md (6d40a079..., commit a2776f7, before
any substrate was downloaded). Every other domain here has sets of tens to
hundreds of members. Metabolomics does not: a pathway is 5-40 compounds and an
assay measures dozens, not thousands. If the size confound is arithmetic it
should still be visible; if it needs large sets to appear, that is a real
boundary and it belongs in the table.

Substrate, both public, no auth:
  MetaboAnalyst example dataset human_cachexia.csv (77 urine samples, cachexic
    vs control, 63 measured metabolites) -- the field's own teaching dataset
  SMPDB metabolite sets (bulk CSV download), mapped by HMDB ID and by
    normalised compound name

Construction, fixed in the pre-registration:
  per-metabolite  Welch t-test on log-transformed concentrations, BH q < 0.05
                  (the default MetaboAnalyst workflow)
  sets            SMPDB pathways, size = mappable measured metabolites
  usable set      >= 3 measured members (the registered deviation for this
                  domain: the 5-member floor used elsewhere would delete the
                  boundary condition this domain exists to probe)

Writes results/domains/metabolite.json. Names no metabolite and no pathway.

    .venv/bin/python -m src.domain_metabolite
"""
from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import ttest_ind

sys.path.insert(0, str(Path("packages/denali-audit").resolve()))
from denali_audit.core import audit, rerank  # noqa: E402

DATA = Path("data/raw/metabolite/human_cachexia.csv")
SMPDB = Path("data/raw/metabolite/smpdb")
CORPUS = Path("results/corpus/corpus_per_screen.csv")
OUT = Path("results/domains/metabolite.json")

MIN_MEMBERS = 3          # registered deviation for this domain
Q = 0.05


def norm(s: str) -> str:
    s = str(s).strip().lower()
    s = re.sub(r"^(l|d|dl)-", "", s)
    s = re.sub(r"[^a-z0-9]", "", s)
    return s


def bh(p: np.ndarray) -> np.ndarray:
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


def main() -> int:
    d = pd.read_csv(DATA)
    grp = d.iloc[:, 1].astype(str).str.lower()
    mets = list(d.columns[2:])
    X = np.log10(d[mets].astype(float).values + 1e-9)
    a, b = X[grp.str.contains("cachexic")], X[~grp.str.contains("cachexic")]
    print(f"{X.shape[0]} samples ({len(a)} vs {len(b)}), {len(mets)} metabolites")
    p = ttest_ind(a, b, equal_var=False, axis=0).pvalue
    q = bh(np.asarray(p, float))
    hit_mask = q < Q
    hits = {norm(m) for m, h in zip(mets, hit_mask) if h}
    measured = {norm(m) for m in mets}
    print(f"{hit_mask.sum()}/{len(mets)} metabolites significant at BH q<{Q}")

    # SMPDB sets, mapped by normalised name (the assay reports names, not IDs)
    sets = defaultdict(set)
    files = sorted(SMPDB.glob("*_metabolites.csv"))
    for i, f in enumerate(files):
        if i % 10000 == 0:
            print(f"  {i}/{len(files)}")
        try:
            t = pd.read_csv(f, usecols=["Pathway Name", "Metabolite Name"],
                            dtype=str, low_memory=False)
        except Exception:
            continue
        if not len(t):
            continue
        pw = str(t["Pathway Name"].iloc[0])
        for m in t["Metabolite Name"].dropna():
            sets[pw].add(norm(m))
    print(f"{len(sets)} SMPDB pathways")

    names, size, nhit = [], [], []
    for nme, mem in sets.items():
        mm = mem & measured
        if len(mm) < MIN_MEMBERS:
            continue
        names.append(nme)
        size.append(len(mm))
        nhit.append(len(mm & hits))

    if len(size) < 8:
        report = {"domain": "metabolite sets",
                  "status": "no defensible number here",
                  "reason": f"only {len(size)} sets reach {MIN_MEMBERS} measured "
                            f"members; the assay measures {len(mets)} compounds"}
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(report, indent=2) + "\n")
        print(json.dumps(report, indent=2))
        return 0

    A = audit(size, nhit)
    rr = rerank(size, nhit, names=names, top=10)
    corpus = pd.read_csv(CORPUS).r2_size_alone.dropna()
    lg = r2_log(size, nhit)
    pct = float((corpus < lg).mean() * 100)

    # ---- DEGENERACY CHECK, and it fires --------------------------------
    # A statistic has a floor and a ceiling set by its design. If nearly every
    # measured metabolite is a hit, then hits = rate x size as an arithmetic
    # identity and the R^2 measures the tautology, not a confound. That is
    # exactly what happens here, so it is stated in the primary result rather
    # than discovered by a reader.
    hit_frac = float(hit_mask.mean())
    degenerate = hit_frac > 0.60
    t = ttest_ind(a, b, equal_var=False, axis=0).statistic
    k = max(1, int(round(0.10 * len(mets))))
    strict = {norm(m) for m in np.array(mets)[np.argsort(-np.abs(t))[:k]]}
    s_names, s_size, s_hit = [], [], []
    for nme, mem in sets.items():
        mm = mem & measured
        if len(mm) >= MIN_MEMBERS:
            s_names.append(nme)
            s_size.append(len(mm))
            s_hit.append(len(mm & strict))
    sens = None
    if len(s_size) >= 8 and sum(s_hit) > 0:
        SA = audit(s_size, s_hit)
        srr = rerank(s_size, s_hit, names=s_names, top=10)
        sens = {
            "label": "POST-HOC, not pre-registered. Added because the registered "
                     "hit rule returned an 86% hit rate, which makes the primary "
                     "number arithmetically forced.",
            "hit_rule": f"top 10% of metabolites by |t| ({k} of {len(mets)})",
            "r2_size_alone_raw": SA["r2_size_alone"],
            "r2_size_alone_log": round(r2_log(s_size, s_hit), 4),
            "verdict": SA["verdict"],
            "corpus_percentile_logsize": round(float(
                (corpus < r2_log(s_size, s_hit)).mean() * 100), 1),
            "rerank_top10_survived": srr["survived_top_n"],
            "sets_with_zero_hits": SA["sets_with_zero_hits"],
        }

    report = {
        "domain": "metabolite sets",
        "status": "Pre-registered in docs/DOMAINS_PREREG.md (6d40a079..., a2776f7).",
        "why_this_domain": "The boundary condition. Sets here are 3-40 members, "
                           "not hundreds. If the confound needs large sets it "
                           "should weaken or vanish here.",
        "substrate": "MetaboAnalyst human_cachexia.csv x SMPDB pathway sets",
        "construction": {
            "hit_rule": f"Welch t on log concentrations, BH q < {Q}",
            "n_samples": int(X.shape[0]),
            "n_metabolites_measured": len(mets),
            "n_metabolites_hit": int(hit_mask.sum()),
            "usable_set_floor": MIN_MEMBERS,
        },
        "n_sets": A["n_sets"],
        "size_range": A["size_range"],
        "median_set_size": int(np.median(size)),
        "r2_size_alone_raw": A["r2_size_alone"],
        "r2_size_alone_log": round(lg, 4),
        "spearman_size_vs_hits": A["spearman_size_vs_hits"],
        "verdict": A["verdict"],
        "corpus_percentile_logsize": round(pct, 1),
        "rerank_top10_survived": rr["survived_top_n"],
        "rerank_top10_left": rr["left_top_n"],
        "sets_with_zero_hits": A["sets_with_zero_hits"],
        "DEGENERACY_WARNING": ({
            "fired": True,
            "hit_fraction": round(hit_frac, 3),
            "why_the_primary_number_is_not_usable": (
                f"{hit_frac:.0%} of measured metabolites are hits, so member "
                f"hits = {hit_frac:.2f} x set size as an arithmetic identity. "
                f"With sets of {A['size_range'][0]}-{A['size_range'][1]} members "
                f"the R^2 of {A['r2_size_alone']} measures that tautology, not a "
                f"confound. THE HEADLINE ENTRY FOR THIS DOMAIN IS THEREFORE THE "
                f"POST-HOC STRICT-HIT VARIANT BELOW, LABELLED AS POST-HOC, AND "
                f"THE PRIMARY IS REPORTED BESIDE IT, NEVER INSTEAD OF IT."),
            "what_it_really_shows": (
                "The boundary condition failed in the opposite direction from "
                "the one anticipated. The problem is not that sets are too "
                "small to show the confound; it is that a 63-compound assay "
                "cannot define a meaningful null against sets of 3-8 members."),
        } if degenerate else {"fired": False,
                              "hit_fraction": round(hit_frac, 3)}),
        "post_hoc_strict_hit_rule": sens or {
            "status": "no defensible number here under the strict rule"},
        "scope": "No metabolite and no pathway is named as a finding.",
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: report[k] for k in
                      ("n_sets", "size_range", "r2_size_alone_raw",
                       "r2_size_alone_log", "verdict", "corpus_percentile_logsize",
                       "rerank_top10_survived")}, indent=2))
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
