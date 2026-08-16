"""Domain (b): metabolite sets. Size-confound audit.

POST-HOC / EXPLORATORY. Nothing here was pre-registered.
No individual pathway, metabolite or compound is named as a finding anywhere in the
outputs. Only distributions and counts leave this script.
"""
from __future__ import annotations

import collections
import json
import os
import re
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, "/tmp/denali-integ-r5rQU4fP/denali/packages/denali-audit")
from denali_audit import audit, audit_replication  # noqa: E402

BASE = "/private/tmp/claude-501/-Users-alexvintera/75f80e10-6294-445d-9fe6-7f72f726786e/scratchpad/met"
OUT = "/tmp/denali-integ-r5rQU4fP/denali/results/breadth/metabolites"
os.makedirs(OUT, exist_ok=True)

RNG = np.random.default_rng(20260816)


def first14(k):
    return k.split("-")[0].strip().upper() if k else None


# ---------------------------------------------------------------- reference data
refmet = json.load(open(f"{BASE}/refmet_all.json"))
name2ik = {}
for v in refmet.values():
    nm = (v.get("name") or "").strip().lower()
    ik = (v.get("inchi_key") or "").strip()
    if nm and ik:
        name2ik.setdefault(nm, ik)
print(f"refmet rows={len(refmet)} names_with_inchikey={len(name2ik)}")

# ------------------------------------------------- measured metabolites per study
studies = json.load(open(f"{BASE}/mw_selected.json"))
study_keys = {}          # study_id -> set of inchikey-first14 actually measured
study_nmets = {}
SKIP = {"", "-", "standard", "unknown", "unidentified"}
for sid in studies:
    p = f"{BASE}/mw_study_mets/{sid}.json"
    if not os.path.exists(p) or os.path.getsize(p) < 5:
        continue
    try:
        d = json.load(open(p))
    except Exception:
        continue
    if not isinstance(d, dict) or not d:
        continue
    names = set()
    for rec in d.values():
        if not isinstance(rec, dict):
            continue
        rn = (rec.get("refmet_name") or "").strip().lower()
        if rn and rn not in SKIP:
            names.add(rn)
    keys = {first14(name2ik[n]) for n in names if n in name2ik}
    keys.discard(None)
    study_nmets[sid] = len(names)
    if keys:
        study_keys[sid] = keys

print(f"studies_fetched={len(study_nmets)} studies_with_resolved_keys={len(study_keys)}")
union_all = set().union(*study_keys.values()) if study_keys else set()
print(f"union measured inchikey-blocks = {len(union_all)}")

# ------------------------------------------------------------------- SMPDB sets
smpdb = json.load(open(f"{BASE}/smpdb_curated.json"))
smpdb_sets = {}
for pid, v in smpdb.items():
    mem = {}
    for mid, hmdb, kegg, ik, mname in v["mets"]:
        b = first14(ik)
        if b:
            mem[b] = (hmdb, kegg)
    if mem:
        smpdb_sets[pid] = mem
print(f"SMPDB curated metabolic sets = {len(smpdb_sets)}")

# -------------------------------------------------------------------- KEGG sets
kegg = json.load(open(f"{BASE}/kegg_sets.json"))
kegg_ik = json.load(open(f"{BASE}/kegg_inchikey_xw.json"))     # KEGG C-id -> InChIKey
kegg_ik_b = {k: first14(v) for k, v in kegg_ik.items()}
GLOBAL_MAPS = {"hsa01100", "hsa01110", "hsa01120", "hsa01200", "hsa01210", "hsa01212",
               "hsa01230", "hsa01232", "hsa01240", "hsa01250", "hsa01220", "hsa01310",
               "hsa01320"}

# ------------------------------------------------------------------ audit driver
# Set identifiers are deliberately replaced by salted opaque tokens before anything
# is written to disk. The unit of inference in this work is the distribution; no
# individual pathway is named as confounded, as clean, or as a candidate.
import hashlib  # noqa: E402

_SALT = b"denali-breadth-metabolites-20260816"


def anon(sid):
    return "set_" + hashlib.sha256(_SALT + sid.encode()).hexdigest()[:10]


results = {}
table_rows = []


def run(label, ids, sizes, hits, note, family):
    sizes = np.asarray(sizes, float)
    hits = np.asarray(hits, float)
    rec = {"label": label, "note": note, "n_sets": int(len(sizes))}
    try:
        r = audit(sizes, hits)
        rec.update({k: r[k] for k in ("n_sets", "size_range", "r2_size_alone",
                                      "spearman_size_vs_hits", "sets_with_zero_hits",
                                      "verdict")})
        rec["fold_size_range"] = round(float(sizes.max() / max(sizes.min(), 1)), 2)
        rec["median_size"] = float(np.median(sizes))
        rec["median_hit_rate"] = round(float(np.median(hits / sizes)), 4)
        rec["error"] = None
        if not np.isfinite(rec["r2_size_alone"]):
            rec["verdict"] = "DEGENERATE -- no variance in hits, R2 undefined"
            rec["degenerate"] = True
    except ValueError as e:
        rec.update({"r2_size_alone": None, "verdict": None, "error": str(e)})
    results[label] = rec
    for i, sid in enumerate(ids):
        table_rows.append({"mapping": label, "family": family,
                           "set_token": anon(sid),
                           "size": int(sizes[i]), "hits": int(hits[i])})
    print(f"  {label:52s} n={rec['n_sets']:4d} r2={rec.get('r2_size_alone')} "
          f"{rec.get('verdict')} {rec.get('error') or ''}")
    return rec


def strata(label_stem, ids, sizes, hits, note, family):
    ids = list(ids)
    sizes = np.asarray(sizes, float)
    hits = np.asarray(hits, float)
    run(label_stem, ids, sizes, hits, note, family)
    for nm, m in (("size_lt20", sizes < 20),
                  ("size_20to40", (sizes >= 20) & (sizes <= 40)),
                  ("size_gt40", sizes > 40)):
        sub = np.where(m)[0]
        run(f"{label_stem} :: {nm}", [ids[i] for i in sub], sizes[sub], hits[sub],
            note + f" | stratum {nm}", family)


print("\n=== MAPPING FAMILY 1: SMPDB curated metabolic pathways, "
      "measured-coverage hits ===")
sids = sorted(smpdb_sets)
sm_sizes = [len(smpdb_sets[s]) for s in sids]

# 1a. union of all resolved human studies
h = [len(set(smpdb_sets[s]) & union_all) for s in sids]
strata("A1 SMPDB x MW-union(all human studies)", sids, sm_sizes, h,
       "hits = pathway members detected in >=1 of the sampled human MW studies",
       "smpdb")

# 1b. single-platform: the study with the largest resolved metabolite coverage
best = sorted(study_keys, key=lambda s: -len(study_keys[s]))[0]
h = [len(set(smpdb_sets[s]) & study_keys[best]) for s in sids]
strata("A2 SMPDB x MW-single-broadest-study", sids, sm_sizes, h,
       f"hits = members detected in one single human study "
       f"({len(study_keys[best])} resolved compounds); single-platform coverage",
       "smpdb")

# 1c. median-sized study
med = sorted(study_keys, key=lambda s: len(study_keys[s]))[len(study_keys) // 2]
h = [len(set(smpdb_sets[s]) & study_keys[med]) for s in sids]
strata("A3 SMPDB x MW-single-median-study", sids, sm_sizes, h,
       f"hits = members detected in one median-coverage human study "
       f"({len(study_keys[med])} resolved compounds)", "smpdb")

# 1d. frequency threshold: detected in >=10% of studies (a stricter 'hit')
cnt = collections.Counter()
for k in study_keys.values():
    cnt.update(k)
thr = max(1, int(0.10 * len(study_keys)))
freq10 = {k for k, c in cnt.items() if c >= thr}
h = [len(set(smpdb_sets[s]) & freq10) for s in sids]
strata("A4 SMPDB x detected-in->=10pct-of-studies", sids, sm_sizes, h,
       f"hits = members detected in >={thr} of {len(study_keys)} studies "
       f"(reproducibly measurable subset, {len(freq10)} compounds)", "smpdb")

# 1e. detection-frequency sweep -- walks the hit rate from ~1 down to ~0 on the SAME
# sets, so the only thing changing between rows is how strict "a hit" is.
sweep = []
for frac in (0.0, 0.01, 0.05, 0.10, 0.25, 0.50, 0.75, 0.90):
    t = max(1, int(round(frac * len(study_keys)))) if frac > 0 else 1
    keep = {k for k, c in cnt.items() if c >= t}
    hh = [len(set(smpdb_sets[s]) & keep) for s in sids]
    lab = f"A5 SMPDB sweep :: detected in >={frac:.0%} of studies"
    r_all = run(lab, sids, sm_sizes, hh,
                f"threshold {t}/{len(study_keys)} studies; {len(keep)} compounds qualify",
                "smpdb_sweep")
    small = np.where(np.asarray(sm_sizes) < 20)[0]
    r_small = run(lab + " :: size_lt20", [sids[i] for i in small],
                  np.asarray(sm_sizes, float)[small], np.asarray(hh, float)[small],
                  "small-set stratum of the same sweep row", "smpdb_sweep")
    sweep.append({"threshold_frac": frac, "n_compounds": len(keep),
                  "median_hit_rate_all": r_all.get("median_hit_rate"),
                  "r2_all": r_all.get("r2_size_alone"),
                  "verdict_all": r_all.get("verdict"),
                  "median_hit_rate_small": r_small.get("median_hit_rate"),
                  "r2_small": r_small.get("r2_size_alone"),
                  "verdict_small": r_small.get("verdict"),
                  "n_small": r_small.get("n_sets"),
                  "zero_hit_sets_all": r_all.get("sets_with_zero_hits")})

print("\n=== MAPPING FAMILY 2: KEGG human pathways ===")
kids_all = sorted(kegg)
kids = [k for k in kids_all if k not in GLOBAL_MAPS and len(kegg[k]["cpds"]) >= 5]
kg_sizes = [len(kegg[k]["cpds"]) for k in kids]

# 2a. measured coverage (via the SMPDB KEGG->InChIKey crosswalk)
h = []
for k in kids:
    hh = 0
    for c in kegg[k]["cpds"]:
        b = kegg_ik_b.get(c)
        if b and b in union_all:
            hh += 1
    h.append(hh)
strata("B1 KEGG x MW-union (measured coverage)", kids, kg_sizes, h,
       "hits = KEGG compounds resolvable via the SMPDB KEGG->InChIKey crosswalk AND "
       "detected in >=1 sampled human MW study. Compounds with no crosswalk entry "
       "can never be hits -- this is a floor, not an unbiased estimate.", "kegg")

# 2b. annotation-coverage only: does the compound have a human-metabolome record?
h = [sum(1 for c in kegg[k]["cpds"] if c in kegg_ik_b) for k in kids]
strata("B2 KEGG x SMPDB/HMDB annotation coverage", kids, kg_sizes, h,
       "hits = KEGG compounds that carry a human-metabolome (SMPDB/HMDB) record. "
       "Pure ANNOTATION coverage; no measurement involved.", "kegg")

# 2c. including global/superpathway maps, to show what they do to the fit
h = [sum(1 for c in kegg[k]["cpds"] if c in kegg_ik_b) for k in kids_all]
run("B3 KEGG (incl. global maps) x annotation coverage", kids_all,
    [len(kegg[k]["cpds"]) for k in kids_all], h,
    "same as B2 but global/superpathway maps and 1-4 compound pathways retained",
    "kegg")

# 2d. the same detection-frequency sweep on the KEGG sets, for a second collection
kegg_sweep = []
for frac in (0.0, 0.05, 0.10, 0.25, 0.50):
    t = max(1, int(round(frac * len(study_keys)))) if frac > 0 else 1
    keep = {k for k, c in cnt.items() if c >= t}
    hh = [sum(1 for c in kegg[k]["cpds"]
              if kegg_ik_b.get(c) in keep) for k in kids]
    lab = f"B4 KEGG sweep :: detected in >={frac:.0%} of studies"
    r_all = run(lab, kids, kg_sizes, hh, f"threshold {t}/{len(study_keys)} studies",
                "kegg_sweep")
    small = np.where(np.asarray(kg_sizes) < 20)[0]
    r_small = run(lab + " :: size_lt20", [kids[i] for i in small],
                  np.asarray(kg_sizes, float)[small], np.asarray(hh, float)[small],
                  "small-set stratum of the same sweep row", "kegg_sweep")
    kegg_sweep.append({"threshold_frac": frac, "n_compounds": len(keep),
                       "median_hit_rate_all": r_all.get("median_hit_rate"),
                       "r2_all": r_all.get("r2_size_alone"),
                       "verdict_all": r_all.get("verdict"),
                       "median_hit_rate_small": r_small.get("median_hit_rate"),
                       "r2_small": r_small.get("r2_size_alone"),
                       "verdict_small": r_small.get("verdict"),
                       "n_small": r_small.get("n_sets")})

print("\n=== REPLICATION ARM ===")
rep = {"computed": False, "note": ""}
order = sorted(study_keys)
RNG.shuffle(order)
half_a, half_b = order[::2], order[1::2]
ka = set().union(*[study_keys[s] for s in half_a])
kb = set().union(*[study_keys[s] for s in half_b])
ha = [len(set(smpdb_sets[s]) & ka) for s in sids]
hb = [len(set(smpdb_sets[s]) & kb) for s in sids]
try:
    rr = audit_replication(sm_sizes, ha, hb)
    rep = {"computed": True,
           "n_paired_sets": rr["n_sets"],
           "raw_agreement": rr["agreement_raw"],
           "after_removing_size": rr["agreement_after_removing_size"],
           "pct_that_is_size": rr["pct_of_agreement_that_is_size"],
           "note": (f"Two disjoint random halves of the {len(study_keys)} resolved "
                    f"human MW studies ({len(half_a)} vs {len(half_b)}) treated as two "
                    f"independent 'screens'. Coverage, not differential abundance.")}
except ValueError as e:
    rep = {"computed": False, "note": str(e)}
print(" ", rep)

# also a two-single-study replication (harsher, genuinely independent platforms)
rep2 = {"computed": False, "note": ""}
top2 = sorted(study_keys, key=lambda s: -len(study_keys[s]))[:2]
ha2 = [len(set(smpdb_sets[s]) & study_keys[top2[0]]) for s in sids]
hb2 = [len(set(smpdb_sets[s]) & study_keys[top2[1]]) for s in sids]
try:
    rr2 = audit_replication(sm_sizes, ha2, hb2)
    rep2 = {"computed": True, "n_paired_sets": rr2["n_sets"],
            "raw_agreement": rr2["agreement_raw"],
            "after_removing_size": rr2["agreement_after_removing_size"],
            "pct_that_is_size": rr2["pct_of_agreement_that_is_size"],
            "note": "Two single broadest-coverage human studies as independent arms."}
except ValueError as e:
    rep2 = {"computed": False, "note": str(e)}
print(" ", rep2)

# ---------------------------------------------------------------------- outputs
CORPUS = {"p10": 0.1026, "p25": 0.1862, "median": 0.2244, "p75": 0.2689, "p90": 0.4548}


def pct(r2):
    if r2 is None or not np.isfinite(r2):
        return None
    pts = [(0.1026, 10), (0.1862, 25), (0.2244, 50), (0.2689, 75), (0.4548, 90)]
    if r2 < pts[0][0]:
        return "<p10"
    if r2 >= pts[-1][0]:
        return ">=p90"
    for (a, pa), (b, pb) in zip(pts, pts[1:]):
        if a <= r2 < b:
            return f"~p{pa}-p{pb}"
    return None


for k, v in results.items():
    v["corpus_percentile"] = pct(v.get("r2_size_alone"))

payload = {
    "domain": "metabolite sets (metabolomics pathway membership vs measured coverage)",
    "label": "POST-HOC / EXPLORATORY -- not pre-registered",
    "unit_of_inference": "the distribution of sets. No individual pathway, compound or "
                         "metabolite is named, ranked or flagged anywhere in this output.",
    "corpus_yardstick": CORPUS,
    "n_mw_studies_fetched": len(study_nmets),
    "n_mw_studies_resolved": len(study_keys),
    "n_measured_inchikey_blocks_union": len(union_all),
    "mappings": results,
    "detection_threshold_sweep_smpdb": sweep,
    "detection_threshold_sweep_kegg": kegg_sweep,
    "saturation_diagnostic": {
        "what": "R2 across every variant plotted against that variant's median hit "
                "rate. When the hit rate saturates near 1 the relation hits ~= size is "
                "arithmetic, not evidence of a biological confound; when it collapses "
                "to 0 the response is degenerate and R2 is noise.",
        "spearman_r2_vs_absdist_from_half": None,
        "spearman_r2_vs_median_hit_rate": None,
        "caveat": "Descriptive only. No threshold was pre-set for either statistic "
                  "and none is applied. Both extremes are pathological for different "
                  "reasons, so a single monotone summary understates the effect; the "
                  "sweep tables are the evidence, not these two numbers.",
    },
    "replication_arm_split_halves": rep,
    "replication_arm_two_studies": rep2,
}
_hr = [(v["median_hit_rate"], v["r2_size_alone"]) for v in results.values()
       if v.get("median_hit_rate") is not None
       and v.get("r2_size_alone") is not None
       and np.isfinite(v["r2_size_alone"])]
if len(_hr) >= 8:
    hrv = np.array([a for a, _ in _hr])
    y = np.array([b for _, b in _hr])
    sd = payload["saturation_diagnostic"]
    sd["spearman_r2_vs_absdist_from_half"] = round(
        float(pd.Series(np.abs(hrv - 0.5)).corr(pd.Series(y), method="spearman")), 4)
    sd["spearman_r2_vs_median_hit_rate"] = round(
        float(pd.Series(hrv).corr(pd.Series(y), method="spearman")), 4)
    sd["n_variants"] = len(_hr)

def _clean(o):
    if isinstance(o, dict):
        return {k: _clean(v) for k, v in o.items()}
    if isinstance(o, list):
        return [_clean(v) for v in o]
    if isinstance(o, float) and not np.isfinite(o):
        return None
    return o


payload = _clean(payload)
json.dump(payload, open(f"{OUT}/metabolite_audit.json", "w"), indent=2,
          allow_nan=False)
pd.DataFrame(table_rows).to_csv(f"{OUT}/sets_standardized.csv", index=False)
print(f"\nwrote {OUT}/metabolite_audit.json and sets_standardized.csv "
      f"({len(table_rows)} rows)")
