import pandas as pd, glob, os, numpy as np
BASE="/Users/alexvintera/Documents/GitHub/crc-metagenomics"
chunks = sorted(glob.glob(BASE+"/data/raw/pathway_chunks/*.csv"))
print([os.path.basename(c) for c in chunks])
meta = pd.read_csv(BASE+"/data/raw/metadata.csv")
full = pd.read_csv(BASE+"/data/raw/pathway_unstratified_full.csv")
print("full shape", full.shape)
lens=[]
for c in chunks:
    n = sum(1 for _ in open(c)) - 1
    lens.append(n)
print("chunk rows", dict(zip([os.path.basename(c)[:-4] for c in chunks], lens)), "sum", sum(lens))
# study of full rows via metadata
sid2study = dict(zip(meta.sample_id, meta.study_name))
full["study"] = full.sample_id.map(sid2study)
off=0
ok=True
for c,n in zip(chunks,lens):
    name=os.path.basename(c)[:-4]
    seg = full.study.iloc[off:off+n]
    print(name, n, "-> studies in full segment:", seg.value_counts().to_dict())
    if not (seg==name).all(): ok=False
    off+=n
print("row-order alignment verified:", ok, "| consumed", off, "of", len(full))
