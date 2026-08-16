"""Sensitivity of the members-measured mapping to the testability threshold and
significance cut. POST-HOC / EXPLORATORY."""
import glob, json, os, sys
import numpy as np, pandas as pd
from scipy.stats import mannwhitneyu
sys.path.insert(0, "/tmp/denali-integ-r5rQU4fP/denali/packages/denali-audit")
from denali_audit import audit, audit_replication
HERE = os.path.dirname(os.path.abspath(__file__)); BASE = "/Users/alexvintera/Documents/GitHub/crc-metagenomics"
OPS = {"(", ")", ",", "+"}
sizes = {}
for line in open(os.path.join(HERE, "metacyc_pathways_structured_filtered_v24_subreactions")):
    if not line.strip(): continue
    pid, _, st = line.partition("\t")
    sizes[pid.strip()] = len({t[1:] if t.startswith("-") else t for t in st.split() if t not in OPS})
meta = pd.read_csv(BASE + "/data/raw/metadata.csv")
full = pd.read_csv(BASE + "/data/raw/pathway_unstratified_full.csv").set_index("sample_id")
sid2study = dict(zip(meta.sample_id, meta.study_name)); sid2cond = dict(zip(meta.sample_id, meta.study_condition))
studies = pd.Series({s: sid2study.get(s) for s in full.index})
pid_of = lambda c: c.split(":", 1)[0].strip() if ":" in c else None
def bh(p):
    p = np.asarray(p, float); n = len(p); q = np.empty(n); prev = 1.0
    for r, i in enumerate(np.argsort(p)[::-1]): prev = min(prev, p[i] * n / (n - r)); q[i] = prev
    return q
cache = {}
for path in sorted(glob.glob(BASE + "/data/raw/pathway_chunks/*.csv")):
    coh = os.path.basename(path)[:-4]; ch = pd.read_csv(path)
    sub = full.loc[full.index[studies.values == coh]]
    key = [c for c in ch.columns if "|" not in c and c in sub.columns][:60]
    m = dict(zip(sub[key].round(6).apply(lambda r: hash(tuple(r)), axis=1).values, sub.index))
    ch.index = [m[h] for h in ch[key].round(6).apply(lambda r: hash(tuple(r)), axis=1).values]
    cond = pd.Series({i: sid2cond.get(i) for i in ch.index})
    scols = [c for c in ch.columns if "|" in c and "s__" in c and pid_of(c.split("|")[0]) in sizes]
    cache[coh] = (ch[scols], cond)
res = []
for thr in [0.05, 0.10, 0.25, 0.50]:
    frames = []
    for coh, (S, cond) in cache.items():
        pres = (S > 0); tcols = list(pres.columns[pres.sum(axis=0) >= thr * len(S)])
        if not tcols: continue
        a = S.loc[cond[cond == "CRC"].index, tcols].values; b = S.loc[cond[cond == "control"].index, tcols].values
        pv = np.ones(len(tcols))
        for j in range(len(tcols)):
            x, y = a[:, j], b[:, j]
            if len(np.unique(np.concatenate([x, y]))) < 3: continue
            try: pv[j] = mannwhitneyu(x, y, alternative="two-sided").pvalue
            except ValueError: pass
        q = bh(pv)
        rec = {}
        for j, c in enumerate(tcols):
            pid = pid_of(c.split("|")[0]); d = rec.setdefault(pid, [0, 0, 0, 0])
            d[0] += 1; d[1] += int(q[j] < 0.10); d[2] += int(q[j] < 0.20); d[3] += int(pv[j] < 0.05)
        frames.append(pd.DataFrame([(coh, k, *v, sizes[k]) for k, v in rec.items()],
                     columns=["cohort", "pid", "members", "fdr10", "fdr20", "nom05", "rxn"]))
    D = pd.concat(frames)
    p = D.groupby("pid").agg(members=("members", "sum"), fdr10=("fdr10", "sum"),
                             fdr20=("fdr20", "sum"), nom05=("nom05", "sum"), rxn=("rxn", "first")).reset_index()
    for hcol in ["fdr10", "fdr20", "nom05"]:
        for szcol, szname in [("members", "membersMeasured"), ("rxn", "reactions")]:
            try: r = audit(p[szcol].values, p[hcol].values)
            except ValueError as e: continue
            res.append(dict(prevalence_threshold=thr, size=szname, hits=hcol, n_sets=r["n_sets"],
                            r2=r["r2_size_alone"], spearman=r["spearman_size_vs_hits"],
                            zero=r["sets_with_zero_hits"], size_range=r["size_range"], verdict=r["verdict"]))
S = pd.DataFrame(res); S.to_csv(os.path.join(HERE, "table_sensitivity.tsv"), sep="\t", index=False)
print(S.to_string(index=False))
