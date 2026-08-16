import re, json, collections
import numpy as np

PATH = "metacyc_pathways_structured_filtered_v24_subreactions"
OPS = {"(", ")", ",", "+"}

rows = []
raw_tokencounts = []
with open(PATH) as f:
    for line in f:
        line = line.rstrip("\n")
        if not line.strip():
            continue
        parts = line.split("\t")
        pid = parts[0].strip()
        struct = "\t".join(parts[1:])
        toks = struct.split()
        rxn_toks = [t for t in toks if t not in OPS]
        # leading '-' encodes direction (reverse), not a distinct reaction
        stripped = [t[1:] if t.startswith("-") else t for t in rxn_toks]
        uniq = set(stripped)
        rows.append((pid, len(uniq), len(rxn_toks)))
        raw_tokencounts.append(len(rxn_toks))

sizes = np.array([r[1] for r in rows])
print("n_pathways", len(rows))
print("size (unique rxn IDs): min %d max %d median %.1f mean %.1f" % (sizes.min(), sizes.max(), np.median(sizes), sizes.mean()))
print("fold range %.1fx" % (sizes.max()/sizes.min()))
for q in [1,5,10,25,50,75,90,95,99]:
    print("  p%-3d %.1f" % (q, np.percentile(sizes,q)))
occ = np.array([r[2] for r in rows])
print("occurrence-count (dup-inclusive): min %d max %d, differs from unique in %d pathways" % (occ.min(), occ.max(), int((occ!=sizes).sum())))
# any operator tokens present?
print("sample of largest/smallest sizes suppressed by design (no pathway named)")
with open("pathway_sizes.tsv","w") as out:
    out.write("pathway_id\tn_unique_reactions\tn_reaction_slots\n")
    for pid,u,o in rows:
        out.write(f"{pid}\t{u}\t{o}\n")
