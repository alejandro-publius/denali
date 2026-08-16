"""POST-HOC, EXPLORATORY size-confounding audit of microbiome functional sets.

size  = number of unique reaction IDs per MetaCyc pathway (HUMAnN v3 structured
        definition file, MetaCyc v24, filtered)
hits  = several alternative result-quantities, each labelled (see README.md)

No pathway is ever named. Distributions and counts only.
"""
import glob, json, os, re, sys
import numpy as np, pandas as pd
from scipy.stats import mannwhitneyu
sys.path.insert(0, "/tmp/denali-integ-r5rQU4fP/denali/packages/denali-audit")
from denali_audit import audit, audit_replication

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = "/Users/alexvintera/Documents/GitHub/crc-metagenomics"
OPS = {"(", ")", ",", "+"}

# ---------- 1. sizes ----------
sizes = {}
for line in open(os.path.join(HERE, "metacyc_pathways_structured_filtered_v24_subreactions")):
    if not line.strip():
        continue
    pid, _, struct = line.partition("\t")
    toks = [t for t in struct.split() if t not in OPS]
    sizes[pid.strip()] = len({t[1:] if t.startswith("-") else t for t in toks})
SZ = pd.Series(sizes, name="size")

# ---------- 2. abundance ----------
meta = pd.read_csv(BASE + "/data/raw/metadata.csv")
full = pd.read_csv(BASE + "/data/raw/pathway_unstratified_full.csv").set_index("sample_id")
sid2study = dict(zip(meta.sample_id, meta.study_name))
sid2cond = dict(zip(meta.sample_id, meta.study_condition))
studies = pd.Series({s: sid2study.get(s) for s in full.index})

def pid_of(col):
    if ":" not in col:
        return None
    return col.split(":", 1)[0].strip()

BH = lambda p: (lambda o, n: np.minimum.accumulate(
    (p[o] * n / (np.arange(n, 0, -1)))[::-1])[::-1])(np.argsort(p)[::-1], len(p))

def bh(pvals):
    p = np.asarray(pvals, float)
    n = len(p)
    order = np.argsort(p)
    q = np.empty(n)
    prev = 1.0
    for rank, i in enumerate(order[::-1]):
        k = n - rank
        prev = min(prev, p[i] * n / k)
        q[i] = prev
    return q

rowsA, rowsB, rowsC = [], [], []
cohort_info = {}
for path in sorted(glob.glob(BASE + "/data/raw/pathway_chunks/*.csv")):
    coh = os.path.basename(path)[:-4]
    ch = pd.read_csv(path)
    unstrat = [c for c in ch.columns if "|" not in c]
    cand = full.index[studies.values == coh]
    sub = full.loc[cand]
    key = [c for c in unstrat if c in sub.columns][:60]
    m = dict(zip(sub[key].round(6).apply(lambda r: hash(tuple(r)), axis=1).values, sub.index))
    ids = [m.get(h) for h in ch[key].round(6).apply(lambda r: hash(tuple(r)), axis=1).values]
    assert all(i is not None for i in ids) and len(set(ids)) == len(ids), coh
    ch.index = ids
    cond = pd.Series({i: sid2cond.get(i) for i in ids})
    ncrc, nctl = int((cond == "CRC").sum()), int((cond == "control").sum())
    cohort_info[coh] = dict(n_samples=len(ch), n_CRC=ncrc, n_control=nctl)

    # --- A: detection breadth (unstratified) ---
    ucols = [c for c in ch.columns if "|" not in c and pid_of(c) in sizes]
    det = (ch[ucols] > 0).sum(axis=0)
    for c in ucols:
        rowsA.append((coh, pid_of(c), sizes[pid_of(c)], int(det[c]), len(ch)))

    # --- B/C: species strata ---
    scols = [c for c in ch.columns if "|" in c and "s__" in c and pid_of(c.split("|")[0]) in sizes]
    if scols:
        S = ch[scols]
        pres = (S > 0)
        keep = pres.columns[pres.sum(axis=0) >= max(5, 0.10 * len(ch))]
        bypid = {}
        for c in scols:
            bypid.setdefault(pid_of(c.split("|")[0]), []).append(c)
        obs = pres.sum(axis=0)
        for pid, cs in bypid.items():
            n_obs = int(sum(obs[c] > 0 for c in cs))
            rowsB.append((coh, pid, sizes[pid], n_obs, len(cs)))
        # C: differential abundance among testable strata
        if ncrc >= 10 and nctl >= 10:
            tcols = [c for c in keep]
            a = S.loc[cond[cond == "CRC"].index, tcols].values
            b = S.loc[cond[cond == "control"].index, tcols].values
            pv = np.ones(len(tcols))
            for j in range(len(tcols)):
                x, y = a[:, j], b[:, j]
                if len(np.unique(np.concatenate([x, y]))) < 3:
                    continue
                try:
                    pv[j] = mannwhitneyu(x, y, alternative="two-sided").pvalue
                except ValueError:
                    pv[j] = 1.0
            q = bh(pv)
            sig = pd.Series(q < 0.10, index=tcols)
            tested = {}
            for c in tcols:
                tested.setdefault(pid_of(c.split("|")[0]), [0, 0])
                tested[pid_of(c.split("|")[0])][0] += 1
                tested[pid_of(c.split("|")[0])][1] += int(sig[c])
            for pid, (nt, ns) in tested.items():
                rowsC.append((coh, pid, sizes[pid], ns, nt))

A = pd.DataFrame(rowsA, columns=["cohort", "pathway_id", "size", "hits", "n_samples"])
B = pd.DataFrame(rowsB, columns=["cohort", "pathway_id", "size", "hits", "n_strata_cols"])
C = pd.DataFrame(rowsC, columns=["cohort", "pathway_id", "size", "hits", "n_tested"])
for df, n in [(A, "A_detection"), (B, "B_species_breadth"), (C, "C_diffabund")]:
    df.to_csv(os.path.join(HERE, f"table_{n}.tsv"), sep="\t", index=False)

# ---------- 3. audits ----------
out = {"cohorts": cohort_info, "size_distribution": {
    "n_pathways_in_definition_file": len(SZ),
    "min": int(SZ.min()), "max": int(SZ.max()), "median": float(SZ.median()),
    "mean": round(float(SZ.mean()), 2), "fold_range": round(float(SZ.max() / SZ.min()), 1),
    "percentiles": {f"p{q}": float(np.percentile(SZ, q)) for q in [10, 25, 50, 75, 90]},
}, "variants": []}

def add(label, s, h, note):
    try:
        r = audit(np.asarray(s), np.asarray(h))
    except ValueError as e:
        out["variants"].append({"label": label, "error": str(e), "note": note}); return None
    r["label"] = label; r["note"] = note
    out["variants"].append(r); return r

# pooled variants (pathway is the unit; cohorts aggregated)
poolA = A.groupby("pathway_id").agg(size=("size", "first"), hits=("hits", "sum"),
                                    n=("n_samples", "sum")).reset_index()
add("A_pooled_detection_samples", poolA["size"], poolA["hits"],
    "hits = number of the 762 pooled samples in which the pathway was detected (>0). DETECTION mapping.")
poolB = B.groupby("pathway_id").agg(size=("size", "first"), hits=("hits", "max")).reset_index()
add("B_pooled_species_breadth_max", poolB["size"], poolB["hits"],
    "hits = max over cohorts of the number of distinct species strata observed for the pathway. RECOVERED-CONTRIBUTOR mapping.")
poolBu = B.groupby("pathway_id").agg(size=("size", "first"), hits=("hits", "mean")).reset_index()
add("B_pooled_species_breadth_mean", poolBu["size"], poolBu["hits"],
    "hits = mean over 7 cohorts of distinct species strata observed. RECOVERED-CONTRIBUTOR mapping.")
poolC = C.groupby("pathway_id").agg(size=("size", "first"), hits=("hits", "sum"),
                                    tested=("n_tested", "sum")).reset_index()
add("C_pooled_diffabund_FDR10", poolC["size"], poolC["hits"],
    "hits = number of species-stratified instances of the pathway significant at BH-FDR<0.10 for CRC vs control, summed over cohorts. DIFFERENTIAL-ABUNDANCE mapping (closest analogue to a gene-set hit count).")

# per-cohort variants
for coh in sorted(cohort_info):
    a = A[A.cohort == coh]
    add(f"A_{coh}", a["size"], a["hits"], "per-cohort DETECTION mapping")
    b = B[B.cohort == coh]
    add(f"B_{coh}", b["size"], b["hits"], "per-cohort RECOVERED-CONTRIBUTOR mapping")
    c = C[C.cohort == coh]
    if len(c):
        add(f"C_{coh}", c["size"], c["hits"], "per-cohort DIFFERENTIAL-ABUNDANCE mapping (FDR<0.10)")

# ---------- 4. concordance ----------
rep = []
for df, tag in [(A, "A_detection"), (B, "B_species_breadth"), (C, "C_diffabund")]:
    cohs = sorted(df.cohort.unique())
    for i in range(len(cohs)):
        for j in range(i + 1, len(cohs)):
            x = df[df.cohort == cohs[i]].set_index("pathway_id")
            y = df[df.cohort == cohs[j]].set_index("pathway_id")
            common = x.index.intersection(y.index)
            if len(common) < 8:
                continue
            r = audit_replication(x.loc[common, "size"], x.loc[common, "hits"], y.loc[common, "hits"])
            r.update(mapping=tag, cohort_a=cohs[i], cohort_b=cohs[j])
            rep.append(r)
out["replication_pairs"] = rep
R = pd.DataFrame(rep)
R.to_csv(os.path.join(HERE, "table_replication_pairs.tsv"), sep="\t", index=False)
out["replication_summary"] = {
    t: {"n_pairs": int((R.mapping == t).sum()),
        "median_raw_agreement": round(float(R[R.mapping == t].agreement_raw.median()), 4),
        "median_after_removing_size": round(float(R[R.mapping == t].agreement_after_removing_size.median()), 4),
        "median_pct_of_agreement_that_is_size": round(float(R[R.mapping == t].pct_of_agreement_that_is_size.median()), 1),
        "IQR_pct_size": [round(float(R[R.mapping == t].pct_of_agreement_that_is_size.quantile(q)), 1) for q in (.25, .75)]}
    for t in R.mapping.unique()}

json.dump(out, open(os.path.join(HERE, "audit_output.json"), "w"), indent=2, default=str)
print(json.dumps({k: out[k] for k in ["size_distribution", "cohorts", "replication_summary"]}, indent=2, default=str))
print("\n--- variants ---")
for v in out["variants"]:
    if "error" in v:
        print(f"{v['label']:<34} ERROR {v['error']}")
    else:
        print(f"{v['label']:<34} n={v['n_sets']:<4} R2={v['r2_size_alone']:<7} rho={v['spearman_size_vs_hits']:<8} zero={v['sets_with_zero_hits']:<4} range={v['size_range']} {v['verdict']}")
