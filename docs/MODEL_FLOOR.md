# Can denali audit a virtual cell model? No — and the position was already occupied

**Not an evaluation.** No statistical verdict, no estimate, no number computed from
data. A reachability-and-applicability ledger plus a prior-art record, in the same
family as [`results/atlas/source_survey.json`](../results/atlas/source_survey.json).
Artifact: [`results/model_floor/`](../results/model_floor/). Module:
`src/model_floor_audit.py`.

**Three candidates surveyed. Zero floors computable. Nine published papers already
occupying the position this work was planned to claim.**

---

## Why this was checked first

The plan behind this work rested on a specific market claim:

> Billions are buying models whose own flagship benchmark cannot show they beat a
> naive baseline. Nobody owns that baseline. Nobody computes it identically across
> datasets. Nobody publishes it. denali does.

**The first sentence is supported. The next three are not.** Establishing that
before building on it was the entire job, because if the premise is wrong then
saying so is worth more than anything built on top of it.

## The first sentence holds

Arc Institute's own [Virtual Cell Challenge 2025
wrap-up](https://arcinstitute.org/news/virtual-cell-challenge-2025-wrap-up) states
that perturbation-prediction models are *"not yet consistently outperforming naive
baselines across all metrics"*, and — more sharply than the plan quoted — that
*"Almost all models performed worse than baseline on MAE."* Both verified verbatim.

## The novelty claim does not

The naive-baseline critique in perturbation prediction is an active, published
literature. Nine entries, each read from a primary source during this work:

| # | work | why it matters |
|--:|---|---|
| 1 | **Ahlmann-Eltze, Huber & Anders.** *Deep-learning-based gene perturbation effect prediction does not yet outperform simple linear baselines.* Nature Methods 22:1657–1661 | The **title is the claim.** Peer-reviewed |
| 2 | **Kernfeld, Yang, Weinstock, Battle & Cahan.** *A comparison of computational methods for expression forecasting.* Genome Biology 26:388 | Cross-method comparison against simple baselines |
| 3 | **Csendes, Sanz, Szalay & Szalai.** *Benchmarking foundation cell models for post-perturbation RNA-seq prediction.* BMC Genomics 26:393 (2025) | Baseline benchmarking of foundation models |
| 4 | **Miller et al.** *Deep Learning-Based Genetic Perturbation Models **Do** Outperform Uninformative Baselines on Well-Calibrated Metrics* (2025) | The published **counter-position** |
| 5 | **Mejia et al.** *Diversity by Design … Well-Calibrated Metrics* (2025) | Metric calibration as the disputed axis |
| 6 | **Wu et al.** *PerturBench* (2025) | A standing benchmark suite for the task |
| 7 | **Viñas Torné et al.** *Systema: … beyond systematic variation.* Nature Biotechnology (2025) | Separating real signal from systematic variation — the same instinct as a construction floor |
| 8 | **Liu, Zhang, Du, Zhao & Wang.** *Effects of Distance Metrics and Scaling on the Perturbation Discrimination Score.* arXiv 2511.16954 | Showed a VCC metric improves under rescaling **while prediction error increases** |
| 9 | **Arc Institute**, VCC 2025 wrap-up | Arc computes and publishes the model-versus-baseline comparison **itself** |

Entry 4 is the one that settles it. The question is not unexamined — it is
**contested in print**, with papers arguing both directions on the basis of which
metrics are well calibrated. A contested question is a harder place to plant a flag
than an empty one, not an easier one.

This is the same shape as [`results/breadth/`](../results/breadth/README.md)
discovering that EGAD shipped node-degree AUROC as a built-in null in 2017. The
project's standing rule is to state the prior art before a reader finds it, and
this is that rule applied to a plan rather than to a method.

## Can the floor be computed for any of them? No, three different ways

Each blocker is labelled, because "no" for three different reasons is three
different facts:

| candidate | reachable | floor | blocker |
|---|---|---|---|
| **Arc VCC 2025 leaderboard** | partial | **no** | **ACCESS** — no per-perturbation predictions and no per-team metric values are published; the leaderboard serves no data to a plain fetch. **Nobody outside the challenge can recompute any team's baseline, naive or otherwise** |
| **PerturbHD** (Bereket & Leskovec, bioRxiv 2026) | yes | **no** | **STRUCTURE** — see below |
| **Arc STATE / Virtual Cell Atlas / Tahoe-100M** | yes | **no** | **SHAPE** — these ship expression matrices, not set-level hit rankings. No size column, no hit column, so denali's quantity does not exist without first running an enrichment pipeline — at which point the floor would describe *that pipeline*, not the model |

**No floor is reported for any candidate, and that is the finding rather than a gap
in the work.** An estimated row would be fabrication and is refused.

## PerturbHD is the interesting row, and it points back at us

[PerturbHD](https://doi.org/10.64898/2026.04.23.719015) evaluates GEARS,
GenePT-embedding linear models, PRESAGE, a constant mean baseline, experimental
replicates, and an LLM prompted to rank, across four CRISPRi Perturb-seq screens.
It is the **only** public model evaluation found that operates on **MSigDB Hallmark
gene sets** — the same collection denali uses — so it is the only candidate where
denali's estimand could exist at all.

It also reports a result that flatters the field, and the plan required that be led
with rather than buried: **current models consistently beat the mean baseline** for
both prioritisation and simulation, while remaining substantially less accurate
than experimental replicates. Prioritisation recall is 25–45% at a 5% experiment
budget against simulation recall of 4–12% at 20% FDR. An LLM prompted to rank,
with no task-specific finetuning, was competitive with the best specialised model.

**And denali still cannot audit it.** PerturbHD defines hits as perturbations in
the **top 2%** of Hallmark gene-set activity. That is a quantile rule, which fixes
the hit count by construction — and by [evaluation 14](HIT_RULE.md) the shipped
`audit()` returns `UNDETERMINED` on exactly that input rather than a floor.

So the one external benchmark whose collection matches ours is one our instrument
must **refuse**. That is the correct behaviour and it was only correct as of
`5f10e28`: until evaluation 14 ran, the tool would have answered such an input with
a negative R² and an all-clear.

## What survives, and it is what the README already claimed

Not a retreat — a narrowing to what the evidence supports.

1. **Different estimand.** All nine entries score a *model's predicted expression*
   against a simple predictor. denali scores a *published gene-set ranking* against
   its own construction quantity. Different objects, different questions; none of
   the nine computes the second.
2. **Different scale.** None characterises the **distribution** of that floor across
   the published literature. They benchmark models on a handful of datasets;
   [`results/corpus/`](../results/corpus/) carries **1,272 screens** scored by
   identical code.
3. **Different form.** None ships the floor as a callable, versioned, citable
   artifact.

`README.md` already says this: *"The method is not novel. The atlas, the scale and
the product are."* **The repository was more honest than the plan.**

## The correction that matters for planning

**denali's instrument is not an audit of virtual cell models, and scaling it will
not make it one.** Evaluation 14 shows why in the single case where the collections
match. Work aimed at auditing those models would be new work against a contested,
well-populated literature — not an unoccupied position — and it would need a
different estimand from the one this project ships.

## Scope

Names published work and public benchmarks, which a prior-art record cannot avoid.
Calls no model bad, no benchmark wrong and no author mistaken: every row reports
what a source says. No gene or gene set is named. Writes
`results/model_floor/` only; reads nothing from `results/frozen/`.

## Reproduce

```bash
.venv/bin/python -m src.model_floor_audit
```
