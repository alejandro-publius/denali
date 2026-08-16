import pandas as pd, glob, os, numpy as np, json
BASE="/Users/alexvintera/Documents/GitHub/crc-metagenomics"
meta = pd.read_csv(BASE+"/data/raw/metadata.csv")
full = pd.read_csv(BASE+"/data/raw/pathway_unstratified_full.csv")
full = full.set_index("sample_id")
sid2study = dict(zip(meta.sample_id, meta.study_name))
studies = pd.Series({s: sid2study.get(s) for s in full.index})

res={}
for c in sorted(glob.glob(BASE+"/data/raw/pathway_chunks/*.csv")):
    name=os.path.basename(c)[:-4]
    ch = pd.read_csv(c)
    unstrat=[x for x in ch.columns if '|' not in x]
    cand = full.index[studies.values==name]
    sub = full.loc[cand]
    shared=[x for x in unstrat if x in sub.columns]
    # build a signature: rounded tuple of first 40 shared cols
    key = shared[:60]
    sig_full = sub[key].round(6).apply(lambda r: hash(tuple(r)), axis=1)
    sig_ch   = ch[key].round(6).apply(lambda r: hash(tuple(r)), axis=1)
    m = dict(zip(sig_full.values, sig_full.index))
    mapped=[m.get(s) for s in sig_ch.values]
    nmatch=sum(x is not None for x in mapped)
    res[name]=dict(n_chunk=len(ch), n_cohort_meta=len(cand), n_matched=nmatch,
                   n_unique=len(set(x for x in mapped if x)), n_shared_cols=len(shared))
    print(name, res[name])
json.dump(res, open("id_match_diagnostic.json","w"), indent=2)
