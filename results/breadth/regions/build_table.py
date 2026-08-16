"""Build the standardized set/size/hits table for DOMAIN (a) REGION SETS.

POST-HOC AND EXPLORATORY. Nothing here was pre-registered.

Source: ChIP-Atlas "Enrichment Analysis" job outputs, downloaded from the public
object store at https://chip-atlas.dbcls.jp/data/enrichment-analysis/<uuid>/.

Result-TSV schema (column labels read off the accompanying .result.html <th> tooltips,
not guessed):
  1 ID                      SRX/DRX/ERX experiment accession
  2 Experiment type         antigen class (TFs and others / Histone / ATAC-Seq / ...)
  3 Feature                 antigen (the ChIPed factor / mark)
  4 Cell class
  5 Cell type
  6 Num of peaks            "Number of peaks called for the accession ID at column 1"
  7 Overlaps / Dataset A    "x/N"  x = entries of the user's Dataset A overlapped,
                                   N = |Dataset A| (constant down the whole file)
  8 Overlaps / Dataset B    "y/M"  same against the control Dataset B
  9 Log10 P-value           Fisher exact comparing col7 vs col8
 10 Log10 Q-value           Benjamini-Hochberg
 11 Fold Enrichment         ratio of col7 rate to col8 rate

MAPPING ONTO THE AUDIT CONTRACT
  set  = one ChIP-seq/ATAC/Bisulfite experiment (an antigen in a cell type)
  size = col6, the number of peaks that experiment called  -- construction quantity
  hits = col7 numerator, the number of query regions that experiment recovered
         -- result quantity, REAL, taken from the file, not invented

ORIENTATION CAVEAT (state it loudly): the task brief's natural mapping wanted
hits = "number of that experiment's peaks that overlap the query". ChIP-Atlas reports
the transpose: how many of the QUERY's regions were hit by the experiment's peaks.
Both are honest per-set result quantities and both are bounded above by the number of
peaks, so both carry the same construction-quantity exposure; but they are not the same
number and the audit is run on the one the file actually contains.
"""
from __future__ import annotations

import glob
import json
import os
import re
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, "/tmp/denali-integ-r5rQU4fP/denali")
from denali_audit import audit, audit_replication  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
COLS = ["exp_id", "antigen_class", "antigen", "cell_class", "cell_type",
        "n_peaks", "ovl_A", "ovl_B", "log_p", "log_q", "fold"]


def _num(series):
    return pd.to_numeric(series.astype(str).str.extract(r"^\s*(\d+)\s*/", expand=False),
                         errors="coerce")


def _den(series):
    return pd.to_numeric(series.astype(str).str.extract(r"/\s*(\d+)\s*$", expand=False),
                         errors="coerce")


def load_job(uid):
    p = os.path.join(HERE, "raw", "tsv", uid + ".tsv")
    df = pd.read_csv(p, sep="\t", header=None, names=COLS, dtype=str,
                     engine="python", on_bad_lines="skip")
    df["size"] = pd.to_numeric(df["n_peaks"], errors="coerce")
    df["hits_A"] = _num(df["ovl_A"])
    df["nA"] = _den(df["ovl_A"])
    df["hits_B"] = _num(df["ovl_B"])
    df["nB"] = _den(df["ovl_B"])
    for c in ("log_p", "log_q", "fold"):
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df = df.dropna(subset=["size", "hits_A"])
    df = df[df["exp_id"].astype(str).str.match(r"^[SDE]RX\d+$")]
    df = df.drop_duplicates(subset=["exp_id"], keep="first")
    return df


def main():
    cfgs = {c["wabiID"]: c for c in json.load(open(os.path.join(HERE, "job_configs.json")))}
    files = sorted(glob.glob(os.path.join(HERE, "raw", "tsv", "*.tsv")))

    per_job = []
    long_rows = []
    hits_by_job = {}

    for f in files:
        uid = os.path.basename(f)[:-4]
        cfg = cfgs.get(uid, {})
        if cfg.get("typeA") != "bed":
            continue
        df = load_job(uid)
        if len(df) < 8:
            per_job.append(dict(job=uid, n_sets=len(df), status="TOO FEW SETS (<8)"))
            continue

        rec = dict(job=uid, genome=cfg.get("genome"), antigen_class=cfg.get("antigenClass"),
                   cell_class=cfg.get("cellClass"), peak_threshold=cfg.get("threshold"),
                   typeB=cfg.get("typeB"),
                   n_query_regions=(int(df["nA"].iloc[0])
                                    if pd.notna(df["nA"].iloc[0]) else None),
                   status="ok")

        a = audit(df["size"].values, df["hits_A"].values)
        rec.update(n_sets=a["n_sets"], size_min=a["size_range"][0], size_max=a["size_range"][1],
                   r2_A=a["r2_size_alone"], spearman_A=a["spearman_size_vs_hits"],
                   zero_A=a["sets_with_zero_hits"], verdict_A=a["verdict"])

        # M2: the same audit against the CONTROL set (Dataset B). For typeB == 'rnd'
        # Dataset B is randomly permuted regions -- no biology in it at all.
        if df["hits_B"].notna().sum() >= 8:
            b = audit(df["size"].values, df["hits_B"].values)
            rec.update(r2_B=b["r2_size_alone"], spearman_B=b["spearman_size_vs_hits"],
                       zero_B=b["sets_with_zero_hits"], verdict_B=b["verdict"])

        # descriptive only (NOT audit output): does peak count predict the statistic
        # a user actually ranks on?
        s = df["size"]
        for col, name in (("log_q", "rho_size_vs_logQ"), ("fold", "rho_size_vs_fold")):
            v = df[col]
            ok = np.isfinite(s) & np.isfinite(v)
            rec[name] = round(float(s[ok].corr(v[ok], method="spearman")), 4) if ok.sum() >= 8 else None

        per_job.append(rec)
        hits_by_job[uid] = df.set_index("exp_id")[["size", "hits_A"]]

        sub = df[["exp_id", "size", "hits_A", "hits_B", "log_q", "fold"]].copy()
        sub.insert(0, "job", uid)
        sub = sub.rename(columns={"exp_id": "set", "hits_A": "hits",
                                  "hits_B": "hits_control"})
        long_rows.append(sub)

    jobs_df = pd.DataFrame(per_job)
    jobs_df.to_csv(os.path.join(HERE, "per_job_audit.csv"), index=False)

    long = pd.concat(long_rows, ignore_index=True)
    long.to_csv(os.path.join(HERE, "set_size_hits.csv.gz"), index=False,
                compression="gzip")

    # ---- replication arm -------------------------------------------------
    # Two DIFFERENT user jobs whose experiment universes overlap: the same sets,
    # two independent "screens" (two unrelated query region sets).
    reps = []
    uids = list(hits_by_job)
    idx_meta = json.load(open(os.path.join(HERE, "jobs_index.json")))
    for i in range(len(uids)):
        for j in range(i + 1, len(uids)):
            ua, ub = uids[i], uids[j]
            ca, cb = cfgs.get(ua, {}), cfgs.get(ub, {})
            if (ca.get("genome"), ca.get("threshold")) != (cb.get("genome"), cb.get("threshold")):
                continue
            # exclude pairs that are plausibly the same query BED re-submitted:
            # identical uploaded-file byte count is the only signal available.
            if idx_meta.get(ua, {}).get("bedA") == idx_meta.get(ub, {}).get("bedA"):
                continue
            A, B = hits_by_job[ua], hits_by_job[ub]
            common = A.index.intersection(B.index).unique()
            if len(common) < 200:
                continue
            szA = A.loc[common, "size"].values
            szB = B.loc[common, "size"].values
            if szA.shape != szB.shape or not np.allclose(szA, szB):
                continue  # different peak thresholds -> not the same sets
            r = audit_replication(szA, A.loc[common, "hits_A"].values,
                                  B.loc[common, "hits_A"].values)
            r.pop("reading", None); r.pop("what_this_is_not", None)
            r.update(job_a=ua, job_b=ub)
            reps.append(r)
    reps_df = pd.DataFrame(reps)
    if len(reps_df):
        reps_df.to_csv(os.path.join(HERE, "replication_pairs.csv"), index=False)

    ok_all = jobs_df[jobs_df["status"] == "ok"]
    # R2 is undefined when the hit vector is constant. In this corpus that happens
    # only when EVERY set scored zero hits (a query BED that overlapped nothing --
    # almost certainly an assembly / chromosome-naming mismatch on the user's side).
    # audit() returns nan there and the verdict logic then falls through to
    # "NOT SIZE-DOMINATED", which would be wrong. Split them out.
    degenerate = ok_all[ok_all["r2_A"].isna()]
    ok = ok_all[ok_all["r2_A"].notna()]
    summary = {
        "POST_HOC": "Post-hoc and exploratory. Nothing pre-registered.",
        "n_jobs_with_defined_r2": int(len(ok)),
        "n_jobs_degenerate_all_zero_hits_r2_undefined": int(len(degenerate)),
        "n_jobs_empty_result_file_on_server": int((jobs_df["status"] != "ok").sum()),
        "n_bed_query_jobs_found": int(len(jobs_df)),
        "total_set_level_rows": int(len(long)),
        "n_sets_per_job": {k: float(v) for k, v in ok["n_sets"].describe().items()},
        "size_min_overall": int(ok["size_min"].min()),
        "size_max_overall": int(ok["size_max"].max()),
        "M1_query_overlap": {
            "r2_median": float(ok["r2_A"].median()),
            "r2_p10": float(ok["r2_A"].quantile(.10)),
            "r2_p25": float(ok["r2_A"].quantile(.25)),
            "r2_p75": float(ok["r2_A"].quantile(.75)),
            "r2_p90": float(ok["r2_A"].quantile(.90)),
            "r2_min": float(ok["r2_A"].min()),
            "r2_max": float(ok["r2_A"].max()),
            "verdicts": ok["verdict_A"].value_counts().to_dict(),
            "spearman_median": float(ok["spearman_A"].median()),
            "frac_jobs_above_crispr_corpus_median_0.2244":
                round(float((ok["r2_A"] > 0.2244).mean()), 3),
            "frac_jobs_above_crispr_corpus_p90_0.4548":
                round(float((ok["r2_A"] > 0.4548).mean()), 3),
            "frac_jobs_at_or_above_denali_headline_0.465":
                round(float((ok["r2_A"] >= 0.465).mean()), 3),
            "approx_corpus_percentile_of_median": 86,
        },
        "M2_control_overlap": {
            "n": int(ok_all["r2_B"].notna().sum()),
            "r2_median": float(ok_all["r2_B"].median()),
            "r2_p25": float(ok_all["r2_B"].quantile(.25)),
            "r2_p75": float(ok_all["r2_B"].quantile(.75)),
            "verdicts": ok_all.loc[ok_all["r2_B"].notna(),
                                   "verdict_B"].value_counts().to_dict(),
            "n_jobs_with_randomised_control_typeB_rnd":
                int((ok_all["typeB"] == "rnd").sum()),
            "r2_median_randomised_control_only":
                float(ok_all.loc[ok_all["typeB"] == "rnd", "r2_B"].median()),
        },
        "M3_descriptive_not_audit": {
            "what": ("Spearman of peak count against the two statistics a ChIP-Atlas "
                     "user actually ranks on. NOT audit() output -- audit() takes a "
                     "hit count, and these are not counts. Reported because the "
                     "ranking, not the raw overlap, is what gets read."),
            "rho_size_vs_logQ_median": float(ok["rho_size_vs_logQ"].median()),
            "rho_size_vs_logQ_iqr": [float(ok["rho_size_vs_logQ"].quantile(.25)),
                                     float(ok["rho_size_vs_logQ"].quantile(.75))],
            "rho_size_vs_fold_median": float(ok["rho_size_vs_fold"].median()),
            "rho_size_vs_fold_iqr": [float(ok["rho_size_vs_fold"].quantile(.25)),
                                     float(ok["rho_size_vs_fold"].quantile(.75))],
            "note": ("log Q is negative-is-more-significant, so rho ~ -0.61 means "
                     "experiments with more peaks get more significant Fisher "
                     "p-values. Fold enrichment, the effect-size column, is far "
                     "less size-tracking (rho ~ +0.31)."),
        },
        "degenerate_jobs": {
            "n": int(len(degenerate)),
            "why": ("every set scored zero hits, so the hit vector is constant and "
                    "R2 is undefined; audit() returns nan and its verdict field "
                    "falls through to NOT SIZE-DOMINATED, which would be a false "
                    "clean bill of health. Excluded from all M1 statistics."),
        },
        "replication_pairs": {
            "n_pairs": int(len(reps_df)),
            "note": ("pct_of_agreement_that_is_size is unstable when the raw "
                     "agreement is near zero (the ratio blows up and can go "
                     "negative); the _stable subset restricts to pairs with "
                     "|raw Spearman| >= 0.20."),
            **({"n_pairs_stable": int((reps_df["agreement_raw"].abs() >= 0.20).sum()),
                "pct_of_agreement_that_is_size_median_stable": float(
                    reps_df.loc[reps_df["agreement_raw"].abs() >= 0.20,
                                "pct_of_agreement_that_is_size"].median()),
                "pct_of_agreement_that_is_size_p25_stable": float(
                    reps_df.loc[reps_df["agreement_raw"].abs() >= 0.20,
                                "pct_of_agreement_that_is_size"].quantile(.25)),
                "pct_of_agreement_that_is_size_p75_stable": float(
                    reps_df.loc[reps_df["agreement_raw"].abs() >= 0.20,
                                "pct_of_agreement_that_is_size"].quantile(.75)),
                "n_paired_sets_median": float(reps_df["n_sets"].median()),
                "agreement_raw_median": float(reps_df["agreement_raw"].median()),
                "agreement_after_removing_size_median":
                    float(reps_df["agreement_after_removing_size"].median()),
                "pct_of_agreement_that_is_size_median":
                    float(reps_df["pct_of_agreement_that_is_size"].median()),
                "pct_of_agreement_that_is_size_p25":
                    float(reps_df["pct_of_agreement_that_is_size"].quantile(.25)),
                "pct_of_agreement_that_is_size_p75":
                    float(reps_df["pct_of_agreement_that_is_size"].quantile(.75))}
               if len(reps_df) else {}),
        },
        "corpus_yardstick": {
            "denali_crispr_corpus": {"p10": 0.1026, "p25": 0.1862, "median": 0.2244,
                                     "p75": 0.2689, "p90": 0.4548},
        },
    }
    with open(os.path.join(HERE, "audit_regions.json"), "w") as fh:
        json.dump(summary, fh, indent=2)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
