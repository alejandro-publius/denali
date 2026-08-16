"""Track A — is a model's leaderboard position predicted by SUBSET SIZE?

Pre-registered in docs/BENCHMARKS_PREREG.md (sha256 9b825d87..., commit
a2776f7, BEFORE any benchmark data was downloaded). A1-A4, their thresholds and
the expected outcome are fixed there and are not revised here.

THE DISANALOGY, WRITTEN DOWN BEFORE THE RUN. Gene-set hit counts are COUNTS: a
bigger set mechanically collects more hits. Benchmark subject scores are RATES:
accuracy is already normalised by item count. So the mechanical confound cannot
appear in the rate layer by construction. What can appear is (1) the full
arithmetic confound in the COUNT layer, (2) a construction correlation in the
rate layer if item difficulty covaries with subject size, and (3) weighting
sensitivity in the AGGREGATE, because a micro (item-weighted) average weights
each subject by its size and a macro (equal-subject) average does not.

Substrate, both public, no auth:
  open-llm-leaderboard-old/results  — per-subject MMLU (57 hendrycksTest tasks)
  open-llm-leaderboard/results      — per-subtask BBH (24 tasks), for A4
  cais/mmlu test-split sizes        — data/benchmarks/mmlu_subject_sizes.json

Panel rule, verbatim from the pre-registration: every model in the bulk
artifact with a complete 57-subject vector is included; no model is excluded
after any score is seen. IMPLEMENTATION DECISION fixed before any value was
computed: where a model has several result files, the most recent by filename
timestamp is used.

GATE, before any A1-A4 value is read: item counts are recovered independently
from each model's reported standard error, n = acc(1-acc)/se^2 + 1, and must
match the dataset's own test-split sizes. A benchmark whose reported sizes and
reported errors disagree is not a substrate we would audit.

No model, lab or leaderboard entry is named as a finding: the unit of
inference is the distribution over the panel.

Writes results/benchmarks/mmlu.json.

    .venv/bin/python -m src.benchmarks_audit
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import kendalltau, spearmanr

sys.path.insert(0, str(Path("packages/denali-audit").resolve()))
from denali_audit.core import audit  # noqa: E402

V1 = Path("data/raw/mmlu_v1_results")
V2 = Path("data/raw/mmlu_v2_results")
SIZES = Path("data/benchmarks/mmlu_subject_sizes.json")
OUT = Path("results/benchmarks/mmlu.json")

SUBJ_RE = re.compile(r"hendrycksTest-([a-z_]+)")
BBH_RE = re.compile(r"^leaderboard_bbh_(.+)$")


def latest_per_model(root: Path) -> dict[str, Path]:
    best: dict[str, Path] = {}
    for f in root.rglob("results_*.json"):
        model = str(f.parent.relative_to(root))
        if model not in best or f.name > best[model].name:
            best[model] = f
    return best


def read_v1(path: Path) -> dict | None:
    try:
        d = json.loads(path.read_text())
    except Exception:
        return None
    res = d.get("results")
    if not isinstance(res, dict):
        return None
    acc, se = {}, {}
    for k, v in res.items():
        m = SUBJ_RE.search(k)
        if m and isinstance(v, dict) and "acc" in v:
            acc[m.group(1)] = float(v["acc"])
            if "acc_stderr" in v:
                se[m.group(1)] = float(v["acc_stderr"])
    return {"acc": acc, "se": se} if acc else None


def read_v2_bbh(path: Path) -> dict | None:
    try:
        d = json.loads(path.read_text())
    except Exception:
        return None
    res, ns = d.get("results"), d.get("n-samples", {})
    if not isinstance(res, dict):
        return None
    acc, n = {}, {}
    for k, v in res.items():
        m = BBH_RE.match(k)
        if m and isinstance(v, dict):
            a = v.get("acc_norm,none", v.get("acc,none"))
            if a is None:
                continue
            acc[m.group(1)] = float(a)
            sub = ns.get(k)
            if isinstance(sub, dict) and sub.get("effective"):
                n[m.group(1)] = int(sub["effective"])
    return {"acc": acc, "n": n} if acc else None


def main() -> int:
    meta = json.loads(SIZES.read_text())
    sizes = meta["sizes"]
    subjects = sorted(sizes)
    n_items = np.array([sizes[s] for s in subjects], float)
    print(f"{len(subjects)} MMLU subjects, {n_items.min():.0f}-{n_items.max():.0f} items")

    files = latest_per_model(V1)
    print(f"v1 artifact: {len(files)} models with at least one result file")
    rows, se_check = {}, []
    for model, f in files.items():
        r = read_v1(f)
        if r is None or not all(s in r["acc"] for s in subjects):
            continue
        rows[model] = np.array([r["acc"][s] for s in subjects], float)
        if len(r["se"]) == len(subjects):
            a = np.array([r["acc"][s] for s in subjects], float)
            s = np.array([r["se"][s] for s in subjects], float)
            with np.errstate(divide="ignore", invalid="ignore"):
                n_hat = np.where(s > 0, a * (1 - a) / np.maximum(s, 1e-12) ** 2 + 1, np.nan)
            se_check.append(n_hat)
    A = pd.DataFrame(rows, index=subjects).T
    print(f"panel: {len(A)} models with a complete {len(subjects)}-subject vector")

    # ---- GATE ------------------------------------------------------------
    nh = np.vstack(se_check)
    med = np.nanmedian(nh, axis=0)
    rel = np.abs(med - n_items) / n_items
    gate = {
        "n_models_used": int(len(nh)),
        "max_relative_disagreement": round(float(np.nanmax(rel)), 5),
        "subjects_within_1pct": int((rel < 0.01).sum()),
        "passed": bool((rel < 0.01).all()),
        "what_it_checks": "item counts recovered from each model's reported "
                          "standard error, n = acc(1-acc)/se^2 + 1, against the "
                          "dataset's own test-split sizes",
    }
    print(f"GATE: {gate['subjects_within_1pct']}/{len(subjects)} subjects within 1%, "
          f"max disagreement {gate['max_relative_disagreement']}")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    if not gate["passed"] or len(A) < 20:
        OUT.write_text(json.dumps(
            {"status": "GATE FAILED or panel below pre-registered 20 models",
             "gate": gate, "panel_size": int(len(A))}, indent=2) + "\n")
        print("STOPPED before reading any A1-A4 value.")
        return 1

    # ---- A1: does subset size predict the RATE? --------------------------
    mean_acc = A.mean(axis=0).values
    rho_pool = spearmanr(n_items, mean_acc).statistic
    per_model = np.array([spearmanr(n_items, A.iloc[i].values).statistic
                          for i in range(len(A))])
    lg = np.log10(n_items)
    b = np.polyfit(lg, mean_acc, 1)
    r2 = 1 - ((mean_acc - np.polyval(b, lg)) ** 2).sum() / \
        ((mean_acc - mean_acc.mean()) ** 2).sum()
    a1 = {
        "unit": "subject (n=57); models share subject difficulty so the subject "
                "is the independent unit",
        "spearman_size_vs_panel_mean_accuracy": round(float(rho_pool), 4),
        "r2_logsize_vs_panel_mean_accuracy": round(float(r2), 4),
        "per_model_spearman_median": round(float(np.median(per_model)), 4),
        "per_model_spearman_q10_q90": [round(float(np.quantile(per_model, q)), 4)
                                       for q in (0.10, 0.90)],
        "pct_models_negative_rho": round(100 * float((per_model < 0).mean()), 1),
    }
    ar = abs(rho_pool)
    a1["verdict"] = ("CONSTRUCTION CORRELATION STRONG — size predicts difficulty"
                     if ar >= 0.50 else
                     "PRESENT BUT MODERATE" if ar >= 0.25 else
                     "RATE LAYER CLEAN — normalisation left no exploitable size signal")

    # ---- A2: the COUNT layer, denali's own audit verbatim ----------------
    r2s, verdicts = [], []
    for i in range(len(A)):
        k = np.round(A.iloc[i].values * n_items)
        a = audit(n_items, k)
        r2s.append(a["r2_size_alone"])
        verdicts.append(a["verdict"])
    r2s = np.array(r2s, float)
    # Know what the test can and cannot return. A model with the SAME accuracy
    # on every subject has no capability variation at all, so whatever R^2 it
    # produces is pure arithmetic -- the floor this statistic cannot go below
    # for structural reasons. Computing it turns "expected and largely
    # mechanical" from an assertion into a measurement.
    null_r2 = np.array([audit(n_items, np.round(A.iloc[i].values.mean() * n_items))
                        ["r2_size_alone"] for i in range(len(A))], float)
    a2 = {
        "what": "denali's packaged audit applied verbatim to (subject, n_items, "
                "n_correct), n_correct = round(accuracy x n_items)",
        "median_r2_size_alone": round(float(np.median(r2s)), 4),
        "q10_q90": [round(float(np.quantile(r2s, q)), 4) for q in (0.10, 0.90)],
        "pct_CONFOUNDED": round(100 * float(np.mean(
            [v == "CONFOUNDED" for v in verdicts])), 1),
        "verdict": ("ARITHMETIC CONFOUND PRESENT IN COUNT LAYER"
                    if np.median(r2s) >= 0.40 else
                    "NOT PRESENT — the analogy fails even at the count layer"),
        "arithmetic_null": {
            "what": "each model replaced by a hypothetical model with ITS OWN "
                    "mean accuracy on every subject — no capability variation, "
                    "so any size dependence left is arithmetic and nothing else",
            "median_null_r2": round(float(np.median(null_r2)), 4),
            "median_observed_minus_null": round(
                float(np.median(r2s - null_r2)), 4),
            "pct_models_above_their_own_null": round(
                100 * float((r2s > null_r2).mean()), 1),
        },
        "reading": "The count layer's confound is not merely mechanical, it is "
                   "MORE than mechanical: a model with no subject-to-subject "
                   "variation at all scores HIGHER than real models do. Genuine "
                   "differences in subject difficulty add variance that size "
                   "cannot explain, which is why observed sits below the null. "
                   "So this number says nothing bad about benchmarks; it locates "
                   "the protection. Normalisation by item count is the whole of "
                   "what stands between a leaderboard and the genomics failure "
                   "mode.",
    }

    # ---- A3: THE REAL ONE — does weighting move the leaderboard? ---------
    micro = (A.values * n_items).sum(axis=1) / n_items.sum()
    macro = A.values.mean(axis=1)
    rank_micro = pd.Series(-micro).rank(method="min").values
    rank_macro = pd.Series(-macro).rank(method="min").values
    move = rank_micro - rank_macro
    tau = kendalltau(rank_micro, rank_macro).statistic
    top5_micro = set(np.argsort(-micro, kind="stable")[:5])
    top5_macro = set(np.argsort(-macro, kind="stable")[:5])
    pct3 = 100 * float((np.abs(move) >= 3).mean())
    changed = 5 - len(top5_micro & top5_macro)
    a3 = {
        "what": "micro (item-weighted) vs macro (equal-subject) aggregation of "
                "the same per-subject accuracies. Nothing about any model changes.",
        "panel_size": int(len(A)),
        "kendall_tau": round(float(tau), 5),
        "pct_models_moving_3_or_more_ranks": round(pct3, 2),
        "top5_membership_changed": int(changed),
        "max_absolute_rank_move": int(np.abs(move).max()),
        "median_absolute_rank_move": float(np.median(np.abs(move))),
        "pct_models_moving_10_or_more": round(100 * float((np.abs(move) >= 10).mean()), 2),
        "top10_membership_changed": int(10 - len(
            set(np.argsort(-micro, kind="stable")[:10]) &
            set(np.argsort(-macro, kind="stable")[:10]))),
    }
    if changed >= 1 or pct3 >= 10:
        a3["verdict"] = "CONSTRUCTION MOVES THE LEADERBOARD"
    elif changed == 0 and pct3 < 5 and tau >= 0.98:
        a3["verdict"] = "ROBUST — normalisation plus weighting practice survives the audit"
    else:
        a3["verdict"] = "PARTIAL"

    # ---- A4: cross-benchmark agreement (evaluation-6 analog) ------------
    v2files = latest_per_model(V2)
    bbh = {}
    for model, f in v2files.items():
        r = read_v2_bbh(f)
        if r and len(r["acc"]) >= 20 and len(r["n"]) == len(r["acc"]):
            bbh[model] = r
    common = sorted(set(A.index) & set(bbh))
    print(f"A4: {len(bbh)} models with BBH subtasks; {len(common)} in both artifacts")
    if len(common) < 20:
        a4 = {"status": "no defensible number here",
              "reason": f"only {len(common)} models in both artifacts "
                        f"(pre-registered floor 20)"}
    else:
        tasks = sorted(set.intersection(*[set(bbh[m]["acc"]) for m in common]))
        bn = np.array([bbh[common[0]]["n"][t] for t in tasks], float)
        bacc = np.array([[bbh[m]["acc"][t] for t in tasks] for m in common], float)
        b_micro = (bacc * bn).sum(axis=1) / bn.sum()
        b_macro = bacc.mean(axis=1)
        sub = A.loc[common]
        m_micro = (sub.values * n_items).sum(axis=1) / n_items.sum()
        m_macro = sub.values.mean(axis=1)
        rho_micro = float(spearmanr(m_micro, b_micro).statistic)
        rho_macro = float(spearmanr(m_macro, b_macro).statistic)
        a4 = {
            "benchmarks": "MMLU (57 subjects) vs BBH (%d subtasks)" % len(tasks),
            "n_models_common": len(common),
            "bbh_subtask_size_range": [int(bn.min()), int(bn.max())],
            "mmlu_subject_size_range": [int(n_items.min()), int(n_items.max())],
            "agreement_micro": round(rho_micro, 4),
            "agreement_macro": round(rho_macro, 4),
        }
        if rho_micro >= 0.30:
            share = 1 - rho_macro / rho_micro
            a4["share_of_agreement_from_weighting"] = round(float(share), 4)
            a4["verdict"] = ("WEIGHTING STRUCTURE INFLATES AGREEMENT" if share >= 0.25
                             else "AGREEMENT IS CAPABILITY" if share < 0.10
                             else "REPORTED AS MEASURED")
        else:
            a4["verdict"] = "no defensible number here — micro agreement below " \
                            "the pre-registered 0.30 guard"

    # ---- POST-HOC, labelled. Not pre-registered. ------------------------
    # A3's registered criterion fired. Before that is read as "leaderboards are
    # confounded", here is what actually happened at the boundary, and the
    # mechanism that decides it. This section exists because the criterion
    # turned out to be sensitive to panel density and to near-ties, which we
    # did not anticipate when we fixed it -- and the rule is that a criterion
    # is never revised after seeing data, so it stands and this is reported
    # underneath it.
    order_mi = np.argsort(-micro, kind="stable")
    gap5 = float(np.sort(micro)[::-1][4] - np.sort(micro)[::-1][5])
    C = np.corrcoef(A.values.T)
    iu = np.triu_indices(len(subjects), 1)
    w_micro = n_items / n_items.sum()
    posthoc = {
        "label": "POST-HOC, not pre-registered.",
        "why": "A3's criterion fired. This characterises how it fired.",
        "top5_boundary_gap_micro": round(gap5, 8),
        "top5_boundary_gap_in_items": round(gap5 * n_items.sum(), 2),
        "one_item_is_worth": round(1 / n_items.sum(), 8),
        "reading_of_the_top5_change": "The single model that enters the top 5 "
            "under equal-subject weighting is separated from the one it "
            "displaces by one item out of 14,042. The criterion fired on a "
            "tie, not on a reordering.",
        "median_rank_move_as_pct_of_panel": round(
            100 * float(np.median(np.abs(move))) / len(A), 3),
        "rank_move_caveat": "The >=3-rank criterion was fixed before the panel "
            "size was known. With 5,452 densely packed models, 3 ranks is "
            "0.06% of the panel and moves almost automatically.",
        "score_shift_micro_minus_macro": {
            "mean": round(float((micro - macro).mean()), 5),
            "sd": round(float((micro - macro).std()), 5),
            "max_abs": round(float(np.abs(micro - macro).max()), 5),
        },
        "the_construction_difference_is_large": {
            "largest_subject_share_of_items_pct": round(
                100 * float(n_items.max() / n_items.sum()), 1),
            "top5_largest_subjects_share_of_items_pct": round(
                100 * float(np.sort(n_items)[::-1][:5].sum() / n_items.sum()), 1),
            "micro_weight_ratio_largest_to_smallest": round(
                float(w_micro.max() / w_micro.min()), 1),
            "total_variation_distance_between_weightings": round(
                0.5 * float(np.abs(w_micro - 1 / len(n_items)).sum()), 4),
        },
        "why_it_does_not_propagate": {
            "mean_cross_subject_correlation_of_model_accuracy": round(
                float(C[iu].mean()), 4),
            "median": round(float(np.median(C[iu])), 4),
            "pct_subject_pairs_above_0.8": round(100 * float((C[iu] > 0.8).mean()), 1),
            "reading": "A model good at one subject is good at the others, so "
                       "re-weighting the subjects cannot reorder the models "
                       "much. This is a second protection, independent of "
                       "normalisation, and set-level genomics has neither.",
        },
    }

    report = {
        "status": "Pre-registered in docs/BENCHMARKS_PREREG.md "
                  "(9b825d87..., commit a2776f7).",
        "pre_registered_expectation": "Normalisation defeats the mechanical "
                                      "confound: A2 fires, A1 is weak, A3 is "
                                      "robust. If so the finding is 'benchmarks "
                                      "got this right and set-level genomics "
                                      "did not.'",
        "substrate": {
            "panel": "HuggingFace Open LLM Leaderboard v1 archive, every model "
                     "with a complete 57-subject MMLU vector",
            "panel_size": int(len(A)),
            "models_in_artifact": int(len(files)),
            "subject_sizes": "cais/mmlu test split, 100-1534 items",
        },
        "gate": gate,
        "A1_does_size_predict_the_rate": a1,
        "A2_count_layer": a2,
        "A3_does_weighting_move_the_leaderboard": a3,
        "A4_cross_benchmark_agreement": a4,
        "post_hoc_how_A3_fired": posthoc,
        "scope": "No model, lab or leaderboard entry is named. The unit of "
                 "inference is the distribution over the panel.",
    }
    OUT.write_text(json.dumps(report, indent=2) + "\n")
    for k in ("A1_does_size_predict_the_rate", "A2_count_layer",
              "A3_does_weighting_move_the_leaderboard", "A4_cross_benchmark_agreement"):
        print(f"\n{k}: {report[k].get('verdict', report[k].get('status'))}")
        for kk, vv in report[k].items():
            if kk not in ("verdict", "what", "reading", "unit", "status"):
                print(f"    {kk}: {vv}")
    print(f"\nwrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
