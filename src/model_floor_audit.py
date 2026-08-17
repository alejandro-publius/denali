"""Can denali's floor be computed for a public perturbation-prediction model?

NOT AN EVALUATION. It issues no statistical verdict and computes no estimate. It
is a reachability-and-applicability ledger plus a prior-art record, in the same
family as results/atlas/source_survey.json. Every row is a fact read from a
primary source during the session that wrote it, with the source recorded.

WHY IT EXISTS. The plan this arm came from asserted that the naive baseline in
perturbation prediction is an unoccupied position: "Nobody owns that baseline.
Nobody computes it identically across datasets. Nobody publishes it." Checking
that before building on it is the whole job, because if it is wrong then the most
important thing this session can produce is saying so.

WHAT IT FOUND. It is wrong, and not marginally. See PRIOR_ART below: the
naive-baseline critique in perturbation prediction is an active published
literature with at least nine entries, including a Nature Methods paper whose
title is the claim, and a published counter-position arguing the opposite. What
survives for denali is narrower and is stated in WHAT_SURVIVES.

No number here is estimated. Where a floor cannot be computed the row says so and
why; an empty row is honest and an estimated row is not.

    .venv/bin/python -m src.model_floor_audit

Writes results/model_floor/ only. Reads nothing from results/frozen/.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "model_floor"

# Each row: what was checked, what was found, and the primary source it was read
# from. `floor_computable` is the question the plan asked. "no" always carries a
# reason, and the reason is either ACCESS (the outputs are not published) or SHAPE
# (they are published but are not a set-level hit ranking, so denali's estimand
# does not exist for them) or STRUCTURE (they are set-level but the hit rule fixes
# the count, so evaluation 14 applies and audit() refuses).
CANDIDATES = [
    {
        "target": "Arc Virtual Cell Challenge 2025 — final leaderboard",
        "reachable": "partial",
        "what_is_public": (
            "Prose results and winners. Arc's own wrap-up states that perturbation "
            "prediction models are 'not yet consistently outperforming naive "
            "baselines across all metrics' and that 'Almost all models performed "
            "worse than baseline on MAE.' Both quoted verbatim from the wrap-up."),
        "per_item_outputs_public": "no",
        "floor_computable": "no",
        "why_not": "ACCESS. No per-perturbation predictions and no per-team metric "
                   "values are published. The leaderboard page is a client-rendered "
                   "application that serves no data to a plain fetch. Nobody outside "
                   "the challenge can recompute any team's baseline, including a "
                   "naive one.",
        "sources": [
            "https://arcinstitute.org/news/virtual-cell-challenge-2025-wrap-up "
            "— both quotes verified verbatim this session",
            "https://virtualcellchallenge.org/ — returns an unpopulated shell",
        ],
    },
    {
        "target": "PerturbHD — Bereket & Leskovec, bioRxiv 2026",
        "reachable": "yes",
        "what_is_public": (
            "Full text. Evaluates GEARS, GenePT-embedding linear models, PRESAGE, a "
            "constant mean baseline, experimental replicates, and an LLM prompted to "
            "rank, across four CRISPRi Perturb-seq screens. Hits are defined as "
            "perturbations in the top 2% of MSigDB Hallmark gene-set activity "
            "estimated with AUCell. Reports that current models consistently beat "
            "the mean baseline for prioritisation and simulation, while remaining "
            "substantially less accurate than experimental replicates."),
        "per_item_outputs_public": "not established",
        "floor_computable": "no",
        "why_not": (
            "STRUCTURE, and this is the interesting row. PerturbHD is the ONLY public "
            "model evaluation found that operates on the same gene-set collection as "
            "denali, so it is the only candidate where denali's estimand could exist "
            "at all. But its hit rule is a top-2% quantile per gene set, which fixes "
            "the hit count by construction. By evaluation 14 the shipped audit() "
            "returns UNDETERMINED on exactly that input rather than a floor. So the "
            "floor is not computable here for a structural reason, not an access one "
            "— and a tool that answered anyway would be issuing a false reassurance."),
        "sources": [
            "doi:10.64898/2026.04.23.719015 — read in full; hit definition, model "
            "list and the baseline comparison all read directly from the text",
        ],
    },
    {
        "target": "Arc STATE / Virtual Cell Atlas / Tahoe-100M",
        "reachable": "yes",
        "what_is_public": "Model weights and single-cell count matrices (h5ad).",
        "per_item_outputs_public": "n/a",
        "floor_computable": "no",
        "why_not": (
            "SHAPE. These ship expression matrices, not set-level hit rankings. There "
            "is no size column and no hit column, so denali's quantity does not "
            "exist for them without first running an enrichment pipeline — at which "
            "point the floor would describe the pipeline this session built, not the "
            "model. results/atlas/source_survey.json reached the same conclusion "
            "independently and recorded it as a shape mismatch."),
        "sources": ["results/atlas/source_survey.json — prior survey, same finding"],
    },
]

# The position the plan claimed was unoccupied. Every entry was read from the
# reference list of doi:10.64898/2026.04.23.719015 during this session.
PRIOR_ART = [
    {"cite": "Ahlmann-Eltze C, Huber W, Anders S. Deep-learning-based gene "
             "perturbation effect prediction does not yet outperform simple linear "
             "baselines. Nature Methods 22:1657-1661.",
     "why_it_matters": "The paper's TITLE is the claim. Peer-reviewed."},
    {"cite": "Kernfeld E, Yang Y, Weinstock JS, Battle A, Cahan P. A comparison of "
             "computational methods for expression forecasting. Genome Biology 26:388.",
     "why_it_matters": "Cross-method comparison against simple baselines."},
    {"cite": "Csendes G, Sanz G, Szalay KZ, Szalai B. Benchmarking foundation cell "
             "models for post-perturbation RNA-seq prediction. BMC Genomics 26:393 "
             "(2025).",
     "why_it_matters": "Baseline benchmarking of foundation models."},
    {"cite": "Miller HE et al. Deep Learning-Based Genetic Perturbation Models Do "
             "Outperform Uninformative Baselines on Well-Calibrated Metrics (2025).",
     "why_it_matters": "The published COUNTER-position. The question is contested in "
                       "the literature, not unexamined — which is a different thing "
                       "from unoccupied, and a stronger reason to be careful."},
    {"cite": "Mejia GM et al. Diversity by Design: Addressing Mode Collapse Improves "
             "scRNA-seq Perturbation Modeling on Well-Calibrated Metrics (2025).",
     "why_it_matters": "Metric calibration as the disputed axis."},
    {"cite": "Wu Y et al. PerturBench: Benchmarking Machine Learning Models for "
             "Cellular Perturbation Analysis (2025).",
     "why_it_matters": "A standing benchmark suite for this task."},
    {"cite": "Vinas Torne R et al. Systema: A framework for evaluating genetic "
             "perturbation response prediction beyond systematic variation. Nature "
             "Biotechnology (2025).",
     "why_it_matters": "Explicitly about separating real signal from systematic "
                       "variation — the same instinct as a construction floor."},
    {"cite": "Liu Q, Zhang Q, Du J, Zhao S, Wang J. Effects of Distance Metrics and "
             "Scaling on the Perturbation Discrimination Score. arXiv 2511.16954.",
     "why_it_matters": "Showed a VCC metric could be improved by rescaling "
                       "predictions while prediction error increased."},
    {"cite": "Arc Institute, Virtual Cell Challenge 2025 wrap-up.",
     "why_it_matters": "Arc computes and publishes the model-versus-baseline "
                       "comparison itself: 'Almost all models performed worse than "
                       "baseline on MAE.' The baseline is not unowned on its own "
                       "flagship benchmark."},
]

WHAT_SURVIVES = (
    "The plan's first sentence holds: Arc's own flagship benchmark reports that "
    "models do not consistently beat naive baselines, and that almost all were worse "
    "than baseline on MAE. What does not hold is the novelty claim attached to it. "
    "Nine published entries above address naive baselines in perturbation "
    "prediction, one of them a Nature Methods paper whose title states the finding "
    "and one an explicit counter-position, so the position is contested rather than "
    "vacant.\n\n"
    "What survives is narrower and is what README.md already claims — 'The method is "
    "not novel. The atlas, the scale and the product are.' Specifically: (1) every "
    "entry above scores a MODEL's predicted expression against a simple predictor, "
    "whereas denali scores a published gene-set RANKING against its own construction "
    "quantity. Those are different estimands over different objects, and none of the "
    "nine computes the second. (2) None characterises the DISTRIBUTION of that floor "
    "across the published literature; they benchmark models on a handful of "
    "datasets, while results/corpus/ carries 1,272 screens scored by identical code. "
    "(3) None ships the floor as a callable, versioned artifact.\n\n"
    "The correction that matters for planning: denali's instrument is not an audit "
    "of virtual cell models and cannot be made into one by scaling it. Evaluation 14 "
    "shows why in the one case where the collections match — PerturbHD's quantile "
    "hit rule is precisely the input on which audit() must refuse."
)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    computable = [c for c in CANDIDATES if c["floor_computable"] == "yes"]
    out = {
        "what_this_is": ("a reachability-and-applicability ledger with a prior-art "
                         "record. NOT an evaluation: no statistical verdict, no "
                         "estimate, no number computed from data."),
        "question_asked": ("can denali's construction-only floor be computed for a "
                           "public perturbation-prediction model's evaluation "
                           "outputs?"),
        "answer": ("No, for three different reasons across three candidates, none of "
                   "which is 'we did not try'. Every row states whether the blocker "
                   "is ACCESS, SHAPE or STRUCTURE."),
        "n_candidates": len(CANDIDATES),
        "n_floors_computable": len(computable),
        "candidates": CANDIDATES,
        "PRIOR_ART": PRIOR_ART,
        "n_prior_art": len(PRIOR_ART),
        "WHAT_SURVIVES": WHAT_SURVIVES,
        "THE PLAN THIS CORRECTS": (
            "The brief this session worked from stated: 'Billions are buying models "
            "whose own flagship benchmark cannot show they beat a naive baseline. "
            "Nobody owns that baseline. Nobody computes it identically across "
            "datasets. Nobody publishes it. denali does.' The first sentence is "
            "supported by Arc's own wrap-up. The next three are not supported and the "
            "prior-art list is why. Recorded here because the brief's own standing "
            "rule says that where a source contradicts it, the source wins and the "
            "brief is to be told it was wrong."),
        "empty_rows_are_deliberate": (
            "No floor is reported for any candidate. That is the finding, not a gap "
            "in the work: an estimated row would be fabrication and is refused."),
        "scope": ("Names published work and public benchmarks, which is unavoidable "
                  "for a prior-art record. Calls no model bad, no benchmark wrong and "
                  "no author mistaken; every row reports what a source says. No gene "
                  "or gene set is named. Writes results/model_floor/ only."),
    }
    (OUT / "model_floor.json").write_text(json.dumps(out, indent=2) + "\n")
    print(f"{len(CANDIDATES)} candidates surveyed, {len(computable)} floors computable")
    for c in CANDIDATES:
        print(f"  {c['target'][:52]:54s} floor={c['floor_computable']:3s} "
              f"({c['why_not'].split('.')[0] if c['why_not'] else '-'})")
    print(f"\nprior art occupying the position: {len(PRIOR_ART)} entries")
    print(f"wrote {OUT}/model_floor.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
