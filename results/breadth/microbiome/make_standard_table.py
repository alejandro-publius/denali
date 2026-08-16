import json, os, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__))
corpus = pd.read_csv("/tmp/denali-integ-r5rQU4fP/denali/results/corpus/corpus_per_screen.csv")["r2_size_alone"].dropna().values
pct = lambda x: None if x is None or not np.isfinite(x) else round(100 * float((corpus < x).mean()), 1)
rows = []
for f, arm in [("audit_output.json", "reaction-count size"), ("audit_output_D.json", "members-measured size")]:
    j = json.load(open(os.path.join(HERE, f)))
    for v in j["variants"]:
        if "error" in v:
            rows.append(dict(arm=arm, variant=v["label"], n_sets=None, r2_size_alone=None,
                             spearman=None, sets_with_zero_hits=None, size_min=None, size_max=None,
                             verdict="ERROR: " + v["error"], corpus_percentile=None, note=v["note"]))
            continue
        r2 = v["r2_size_alone"]; r2 = None if not np.isfinite(r2) else r2
        rows.append(dict(arm=arm, variant=v["label"], n_sets=v["n_sets"], r2_size_alone=r2,
                         spearman=None if not np.isfinite(v["spearman_size_vs_hits"]) else v["spearman_size_vs_hits"],
                         sets_with_zero_hits=v["sets_with_zero_hits"], size_min=v["size_range"][0],
                         size_max=v["size_range"][1], verdict=v["verdict"],
                         corpus_percentile=pct(r2), note=v["note"]))
T = pd.DataFrame(rows)
T.to_csv(os.path.join(HERE, "standardized_table.tsv"), sep="\t", index=False)
merged = {"domain": "microbiome functional sets (HUMAnN MetaCyc pathways)",
          "label": "POST-HOC, EXPLORATORY, NOT PRE-REGISTERED",
          "reaction_size_arm": json.load(open(os.path.join(HERE, "audit_output.json"))),
          "members_measured_arm": json.load(open(os.path.join(HERE, "audit_output_D.json")))}
json.dump(merged, open(os.path.join(HERE, "audit_output_combined.json"), "w"), indent=2, default=str)
print(T[["arm", "variant", "n_sets", "r2_size_alone", "spearman", "corpus_percentile", "verdict"]].to_string(index=False))
