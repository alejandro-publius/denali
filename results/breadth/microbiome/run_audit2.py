"""Second size definition: size = members MEASURED (species-stratified instances
of the pathway in that cohort's feature table), hits = members significant.
This is denali's exact estimand (members measured vs members significant),
applied to the microbiome's operative unit of testing.
POST-HOC / EXPLORATORY.
"""
import glob, json, os, sys
import numpy as np, pandas as pd
from scipy.stats import mannwhitneyu
sys.path.insert(0, "/tmp/denali-integ-r5rQU4fP/denali/packages/denali-audit")
from denali_audit import audit, audit_replication

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = "/Users/alexvintera/Documents/GitHub/crc-metagenomics"
OPS = {"(", ")", ",", "+"}
sizes = {}
for line in open(os.path.join(HERE, "metacyc_pathways_structured_filtered_v24_subreactions")):
    if not line.strip(): continue
    pid, _, struct = line.partition("\t")
    toks = [t for t in struct.split() if t not in OPS]
    sizes[pid.strip()] = len({t[1:] if t.startswith("-") else t for t in toks})

meta = pd.read_csv(BASE + "/data/raw/metadata.csv")
full = pd.read_csv(BASE + "/data/raw/pathway_unstratified_full.csv").set_index("sample_id")
sid2study = dict(zip(meta.sample_id, meta.study_name)); sid2cond = dict(zip(meta.sample_id, meta.study_condition))
studies = pd.Series({s: sid2study.get(s) for s in full.index})
pid_of = lambda c: c.split(":", 1)[0].strip() if ":" in c else None

def bh(p):
    p = np.asarray(p, float); n = len(p); q = np.empty(n); prev = 1.0
    for rank, i in enumerate(np.argsort(p)[::-1]):
        prev = min(prev, p[i] * n / (n - rank)); q[i] = prev
    return q

rows = []
for path in sorted(glob.glob(BASE + "/data/raw/pathway_chunks/*.csv")):
    coh = os.path.basename(path)[:-4]
    ch = pd.read_csv(path)
    unstrat = [c for c in ch.columns if "|" not in c]
    sub = full.loc[full.index[studies.values == coh]]
    key = [c for c in unstrat if c in sub.columns][:60]
    m = dict(zip(sub[key].round(6).apply(lambda r: hash(tuple(r)), axis=1).values, sub.index))
    ch.index = [m[h] for h in ch[key].round(6).apply(lambda r: hash(tuple(r)), axis=1).values]
    cond = pd.Series({i: sid2cond.get(i) for i in ch.index})
    scols = [c for c in ch.columns if "|" in c and "s__" in c and pid_of(c.split("|")[0]) in sizes]
    S = ch[scols]
    pres = (S > 0)
    tcols = list(pres.columns[pres.sum(axis=0) >= max(5, 0.10 * len(ch))])
    a = S.loc[cond[cond == "CRC"].index, tcols].values
    b = S.loc[cond[cond == "control"].index, tcols].values
    pv = np.ones(len(tcols))
    for j in range(len(tcols)):
        x, y = a[:, j], b[:, j]
        if len(np.unique(np.concatenate([x, y]))) < 3: continue
        try: pv[j] = mannwhitneyu(x, y, alternative="two-sided").pvalue
        except ValueError: pv[j] = 1.0
    q = bh(pv)
    agg = {}
    for j, c in enumerate(tcols):
        pid = pid_of(c.split("|")[0])
        d = agg.setdefault(pid, [0, 0, 0])
        d[0] += 1; d[1] += int(q[j] < 0.10); d[2] += int(pv[j] < 0.05)
    for pid, (nt, nsig, nnom) in agg.items():
        rows.append((coh, pid, nt, nsig, nnom, sizes[pid]))

D = pd.DataFrame(rows, columns=["cohort", "pathway_id", "size_members_measured",
                                "hits_FDR10", "hits_nominal05", "size_reactions"])
D.to_csv(os.path.join(HERE, "table_D_members_measured.tsv"), sep="\t", index=False)

out = {"variants": [], "replication_pairs": []}
def add(label, s, h, note):
    s = np.asarray(s, float); h = np.asarray(h, float)
    try: r = audit(s, h)
    except ValueError as e:
        out["variants"].append({"label": label, "error": str(e), "note": note}); return
    if not np.isfinite(r["r2_size_alone"]):
        r["verdict"] = "DEGENERATE (no variance in hits) - no defensible number"
    r["label"] = label; r["note"] = note; out["variants"].append(r)

pool = D.groupby("pathway_id").agg(members=("size_members_measured", "sum"),
                                   fdr=("hits_FDR10", "sum"), nom=("hits_nominal05", "sum"),
                                   rxn=("size_reactions", "first")).reset_index()
add("D_pooled_membersMeasured_vs_FDR10", pool["members"], pool["fdr"],
    "size = number of species-stratified instances of the pathway TESTED (pooled over 7 cohorts); hits = number significant at BH-FDR<0.10. denali's exact estimand.")
add("D_pooled_membersMeasured_vs_nominal05", pool["members"], pool["nom"],
    "same size; hits = number significant at nominal p<0.05 (uncorrected). Nominal, not FDR.")
add("E_pooled_reactions_vs_nominal05", pool["rxn"], pool["nom"],
    "size = MetaCyc reaction count; hits = nominal p<0.05 count. Reaction-size definition for comparison.")
for coh, g in D.groupby("cohort"):
    add(f"D_{coh}_FDR10", g["size_members_measured"], g["hits_FDR10"], "per-cohort, size = members measured, hits = FDR<0.10")
    add(f"D_{coh}_nominal05", g["size_members_measured"], g["hits_nominal05"], "per-cohort, size = members measured, hits = nominal p<0.05")

cohs = sorted(D.cohort.unique())
for hcol, tag in [("hits_FDR10", "D_FDR10"), ("hits_nominal05", "D_nominal05")]:
    for i in range(len(cohs)):
        for j in range(i + 1, len(cohs)):
            x = D[D.cohort == cohs[i]].set_index("pathway_id"); y = D[D.cohort == cohs[j]].set_index("pathway_id")
            cm = x.index.intersection(y.index)
            if len(cm) < 8: continue
            sz = (x.loc[cm, "size_members_measured"] + y.loc[cm, "size_members_measured"]) / 2.0
            try: r = audit_replication(sz, x.loc[cm, hcol], y.loc[cm, hcol])
            except Exception as e: continue
            r.update(mapping=tag, cohort_a=cohs[i], cohort_b=cohs[j]); out["replication_pairs"].append(r)
R = pd.DataFrame(out["replication_pairs"])
R.to_csv(os.path.join(HERE, "table_replication_pairs_D.tsv"), sep="\t", index=False)
out["replication_summary"] = {}
for t, g in R.groupby("mapping"):
    g2 = g[np.isfinite(g.pct_of_agreement_that_is_size)]
    out["replication_summary"][t] = {"n_pairs": int(len(g)), "n_pairs_finite": int(len(g2)),
        "median_raw_agreement": round(float(g2.agreement_raw.median()), 4),
        "median_after_removing_size": round(float(g2.agreement_after_removing_size.median()), 4),
        "median_pct_of_agreement_that_is_size": round(float(g2.pct_of_agreement_that_is_size.median()), 1),
        "IQR_pct_size": [round(float(g2.pct_of_agreement_that_is_size.quantile(q)), 1) for q in (.25, .75)]}
json.dump(out, open(os.path.join(HERE, "audit_output_D.json"), "w"), indent=2, default=str)
for v in out["variants"]:
    if "error" in v: print(f"{v['label']:<40} ERROR {v['error']}")
    else: print(f"{v['label']:<40} n={v['n_sets']:<4} R2={v['r2_size_alone']:<8} rho={v['spearman_size_vs_hits']:<8} zero={v['sets_with_zero_hits']:<4} range={v['size_range']} {v['verdict']}")
print(json.dumps(out["replication_summary"], indent=2))
