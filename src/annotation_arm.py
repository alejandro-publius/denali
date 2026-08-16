"""Does the confound get worse as the annotation gets looser?

PRE-REGISTERED. Thresholds and the sampling rule fixed in
docs/ANNOTATION_PREREG.md (sha256 ec5edb90…, committed 10a82a7) BEFORE this file
existed or any set outside Hallmark was scored.

Everything this project measured used Hallmark: 50 hand-curated sets spanning 6x
in size. Biologists use Reactome (1,839 sets, 299x) and GO Biological Process
(7,538 sets, 398x). If size drives apparent reversibility, the collection people
actually use should be the worst affected.

Runs on Modal because 800 sets is roughly two CPU-hours locally. The byte-frozen
scorer runs unmodified; only the substrate path is set, on the module object.

    modal run src/annotation_arm.py                # full pre-registered arm
    modal run src/annotation_arm.py --per 20       # smoke test

Writes results/annotation/ ONLY.
"""
from __future__ import annotations

import modal

app = modal.App("denali-annotation")

image = (
    modal.Image.debian_slim(python_version="3.12")
    .pip_install("h5py==3.16.0", "numpy==2.5.2", "pandas==3.0.5",
                 "scipy==1.18.0", "statsmodels==0.14.6")
    .add_local_dir("src", remote_path="/root/src")
    .add_local_dir("data/genesets", remote_path="/root/data/genesets")
)
substrate = modal.Volume.from_name("denali-substrate", create_if_missing=True)

COLLECTIONS = {
    "hallmark": "h.all.v2026.1.Hs.symbols.gmt",
    "wikipathways": "c2.cp.wikipathways.v2026.1.Hs.symbols.gmt",
    "reactome": "c2.cp.reactome.v2026.1.Hs.symbols.gmt",
    "go_bp": "c5.go.bp.v2026.1.Hs.symbols.gmt",
}
SEED = 20260815
PER_COLLECTION = 250
HALLMARK_R2 = 0.4649          # the bar, from results/sensitivity/stripped_model.json
MIN_SCOREABLE = 150


def _load(path: str) -> dict[str, list[str]]:
    out = {}
    with open(path) as fh:
        for line in fh:
            p = line.rstrip("\n").split("\t")
            if len(p) > 2:
                out[p[0]] = [g for g in p[2:] if g]
    return out


def sample_sets(gmt_dir: str, per: int) -> dict[str, list[str]]:
    """Stratified sample across size deciles, seeded, drawn before any scoring."""
    import numpy as np

    rng = np.random.default_rng(SEED)
    picked: dict[str, list[str]] = {}
    for coll, fname in COLLECTIONS.items():
        sets = _load(f"{gmt_dir}/{fname}")
        names = sorted(sets)
        if coll == "hallmark" or len(names) <= per:
            chosen = names                     # Hallmark is used in full
        else:
            sizes = np.array([len(sets[n]) for n in names])
            deciles = np.quantile(sizes, np.linspace(0, 1, 11))
            chosen = []
            for lo, hi in zip(deciles[:-1], deciles[1:]):
                band = [n for n, s in zip(names, sizes) if lo <= s <= hi]
                if not band:
                    continue
                k = min(len(band), per // 10)
                chosen += list(rng.choice(band, size=k, replace=False))
            chosen = sorted(set(chosen))
        for n in chosen:
            picked[f"{coll}||{n}"] = sets[n]
    return picked


@app.function(image=image, volumes={"/substrate": substrate},
              timeout=5400, cpu=2.0, memory=8192)
def score_shard(items: list[tuple[str, list[str]]]) -> list[dict]:
    import os
    import sys
    import pathlib

    os.chdir("/root")
    sys.path.insert(0, "/root")

    import numpy as np
    from scipy.stats import norm
    from statsmodels.stats.multitest import multipletests

    from src import score_k562 as SC

    SC.K562 = pathlib.Path("/substrate/K562_gwps_normalized_bulk_01.h5ad")
    X, symbols, pert, targets = SC.load_k562()

    rows = []
    for key, genes in items:
        coll, name = key.split("||", 1)
        u_z, cos, delta, n_present = SC.score(X, symbols, genes)
        if n_present < 2 or not np.isfinite(u_z).any():
            rows.append({"collection": coll, "set": name, "n_declared": len(genes),
                         "n_present": int(n_present), "scoreable": False})
            continue
        p = 2 * norm.sf(np.abs(u_z))
        ok = np.isfinite(p)
        q = np.full_like(p, np.nan)
        if ok.sum():
            q[ok] = multipletests(p[ok], method="fdr_bh")[1]
        n_hits = int(np.nansum(q < 0.05))
        rows.append({"collection": coll, "set": name, "n_declared": len(genes),
                     "n_present": int(n_present), "n_hits_q05": n_hits,
                     "R_p": round(float(np.log10(1 + n_hits)), 4),
                     "scoreable": True})
    return rows


@app.local_entrypoint()
def main(per: int = PER_COLLECTION, shards: int = 16):
    import hashlib
    import json
    import time
    from pathlib import Path

    import numpy as np
    import pandas as pd
    import statsmodels.api as sm
    from scipy.stats import spearmanr

    root = Path(__file__).resolve().parents[1]
    pre = hashlib.sha256((root / "docs" / "ANNOTATION_PREREG.md").read_bytes()).hexdigest()
    if pre != "ec5edb900ce8fe6ae7615464b8f7f290d8f4c8569ba340533028c546c6ee41e0":
        raise SystemExit(f"pre-registration changed ({pre[:16]}). Thresholds may "
                         "not be revised after the fact. Arm abandoned.")
    scorer = hashlib.sha256((root / "src" / "score_k562.py").read_bytes()).hexdigest()
    if not scorer.startswith("2abfdc6f"):
        raise SystemExit(f"scorer hash {scorer[:16]} is not the frozen one.")

    picked = sample_sets(str(root / "data" / "genesets"), per)
    items = sorted(picked.items())
    print(f"{len(items)} sets sampled across {len(COLLECTIONS)} collections "
          f"(seed {SEED}, stratified by size decile)")

    groups = [items[i::shards] for i in range(shards)]
    groups = [g for g in groups if g]
    t0 = time.time()
    out = [r for chunk in score_shard.map(groups) for r in chunk]
    wall = time.time() - t0
    print(f"scored in {wall:.0f}s across {len(groups)} containers")

    S = pd.DataFrame(out)
    D = root / "results" / "annotation"
    D.mkdir(parents=True, exist_ok=True)
    S.to_csv(D / "sets_scored.csv", index=False)

    per_coll, verdicts = {}, {}
    for coll in COLLECTIONS:
        d = S[(S.collection == coll) & S.scoreable]
        n_ok = len(d)
        rec = {"n_sampled": int((S.collection == coll).sum()),
               "n_scoreable": int(n_ok),
               "size_range": [int(S[S.collection == coll].n_declared.min()),
                              int(S[S.collection == coll].n_declared.max())]}
        if n_ok < (MIN_SCOREABLE if coll != "hallmark" else 35):
            rec["verdict"] = "UNDERPOWERED"
        else:
            fit = sm.OLS(d.R_p, sm.add_constant(d.n_present)).fit()
            rec["size_alone_r2"] = round(float(fit.rsquared), 4)
            rec["slope"] = round(float(fit.params.iloc[1]), 6)
            rec["p"] = float(f"{fit.pvalues.iloc[1]:.4g}")
            rec["exceeds_hallmark_bar"] = bool(rec["size_alone_r2"] >= HALLMARK_R2)
        per_coll[coll] = rec
        verdicts[coll] = rec.get("size_alone_r2")

    go_ok = per_coll["go_bp"].get("exceeds_hallmark_bar", False)
    re_ok = per_coll["reactome"].get("exceeds_hallmark_bar", False)
    verdict = ("CONFOUND WORSENS WITH LOOSER ANNOTATION" if (go_ok and re_ok)
               else "PARTIAL" if (go_ok or re_ok)
               else "DOES NOT SCALE WITH ANNOTATION LOOSENESS")
    claim = "(a)" if (go_ok and re_ok) else "neither" if not (go_ok or re_ok) else "partial"

    ranges = [per_coll[c]["size_range"][1] / max(1, per_coll[c]["size_range"][0])
              for c in COLLECTIONS if "size_alone_r2" in per_coll[c]]
    r2s = [per_coll[c]["size_alone_r2"] for c in COLLECTIONS
           if "size_alone_r2" in per_coll[c]]
    rho, prho = (spearmanr(ranges, r2s) if len(r2s) >= 3 else (float("nan"),) * 2)

    res = {
        "preregistration": {"file": "docs/ANNOTATION_PREREG.md", "sha256": pre,
                            "committed": "10a82a7",
                            "committed_before_this_ran": True},
        "scorer_sha256": scorer, "scorer_unmodified": True,
        "seed": SEED, "sets_scored": int(len(S)),
        "hallmark_bar": HALLMARK_R2,
        "per_collection": per_coll,
        "verdict": verdict, "claim_supported": claim,
        "secondary_descriptive": {
            "spearman_size_range_vs_r2": None if np.isnan(rho) else round(float(rho), 4),
            "p": None if np.isnan(prho) else float(f"{prho:.4g}"),
            "note": "Descriptive. No threshold was set for this and none is applied.",
        },
        "scope": ("Collection-level statistics only. No set is named as a finding. "
                  "Nested parent/child overlap in Reactome and GO is part of what "
                  "is being measured, disclosed rather than adjusted away."),
        "does_not_revise": "the pre-registered K562 primary in results/frozen/",
    }
    (D / "annotation_evaluation.json").write_text(json.dumps(res, indent=2) + "\n")

    print("\n" + "=" * 70)
    for c, r in per_coll.items():
        if "size_alone_r2" in r:
            print(f"  {c:14s} {r['n_scoreable']:4d} sets  size {r['size_range'][0]:>4}-"
                  f"{r['size_range'][1]:<5} R2={r['size_alone_r2']:.4f}"
                  f"{'  ** exceeds Hallmark' if r['exceeds_hallmark_bar'] else ''}")
        else:
            print(f"  {c:14s} {r['verdict']}")
    print(f"\n  bar (Hallmark)  : {HALLMARK_R2}")
    print(f"  VERDICT         : {verdict}")
    print("=" * 70)
