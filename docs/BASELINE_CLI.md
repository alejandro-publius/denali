# `denali baseline` — the naive baseline as something you can call

Arc Institute's Virtual Cell Challenge 2025 drew **5,000+ registrants from 114
countries, 1,200+ teams and 300+ final submissions**, and its own
[wrap-up](https://arcinstitute.org/news/virtual-cell-challenge-2025-wrap-up)
reports that perturbation-prediction models are *"not yet consistently
outperforming naive baselines across all metrics"*, with the winning approaches
*"combining deep learning with classical statistical features"*. Arc's own
[STATE model](https://arcinstitute.org/news/virtual-cell-model-state) is trained
on 167M observational and 100M perturbational cells across 70 human cell
contexts. The baseline is the thing the field keeps failing to clear, and it is
the one number nobody ships.

Every team that reports *"our model beats baseline"* computes its own baseline,
differently, and unaudited. `denali baseline` makes it a callable artifact:

```bash
denali baseline my_predictions.csv --predicted model_score --metric spearman
```

> On spearman, your predictions score 0.5882 and a predictor that sees only how
> big each set is scores 0.5994. Your model does not beat size alone: size alone
> is ahead by 0.0112.

**The metric is asked for and never inferred.** A baseline scored with a
different metric than yours is not a comparison, so the tool refuses rather than
guessing — and if your metric is not one of the six it implements, `--metric
none` hands back the baseline's per-set predictions for you to score yourself.

**The baseline never saw the row it predicts.** For metrics that read the
values, it is a leave-one-out least-squares fit of your truth column on set
size, in whichever of two stated parameterisations predicts better out of
sample. For metrics that read only the order, it is set size itself — unfitted,
because fitting anything there costs rank accuracy the baseline should not lose.
That distinction was not a design instinct: the first version fitted everything,
and a "model" that was literally set size times thirty came out ahead of it on
Spearman, 0.9091 to 0.8252. Under the current baseline the same model ties
exactly, which is the correct answer, and `tests/test_mcp_stdio.py` asserts it.

**This is a measurement, not a verdict.** It does not rank models, it is not a
leaderboard entry, and it is not a claim that any model is bad — a model can be
worth having and not beat this. Arc's finding is a published conclusion about a
benchmark, not evidence against anyone's model, and this tool does not turn it
into one.

**The method is not novel and the README says so before a reader finds out.**
EGAD has shipped node-degree AUROC as a built-in null since 2017
([doi:10.1093/bioinformatics/btw695](https://doi.org/10.1093/bioinformatics/btw695)),
Crow et al. PNAS 2019 did the cross-dataset version, and GREAT
([doi:10.1038/nbt.1630](https://doi.org/10.1038/nbt.1630)) already corrects
region-size bias. What is new here is that the null is packaged, versioned and
callable from a CLI, an MCP tool and a browser — not that anyone thought of it
first.
