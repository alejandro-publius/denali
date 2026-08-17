# Pre-registration — evaluation 13, is the floor predictable from design alone?

**Sealed before any model was fitted.** Hash, commit, then run
`src/floor_law.py`. Deviations are appended below as corrections, never folded
into the text above.

## The question

`results/breadth/` found the boundary condition this project calls scope limit
6: the no-biology value of an `audit()` R² is **not zero**, and it depends
entirely on how `hits` was defined. Where hits are counted over the set's own
members, a large R² is arithmetic before it is a confound.

That was established across three non-gene-set domains with one screen each,
which is enough to find a boundary and nowhere near enough to fit anything. The
question it raises and cannot answer:

**Can a screen's no-biology floor be predicted from how the screen was
constructed, before any biology is measured?**

If it can, then the floor is not a property of the experiment's findings at all
— it is a property of its design, computable in advance, and the honest way to
report an enrichment result would be to state the expected floor alongside it.

## Population

The **1,272 screens already in `results/corpus/corpus_per_screen.csv`**. No new
data, no download, no Modal. Every screen shares one mapping structure — hits
are counted over each Hallmark set's own members, so `hits ≤ size` throughout —
which means **mapping structure is constant here and cannot be a predictor.**
This arm therefore tests a strictly narrower question than the cross-domain law
the breadth arm gestured at, and the narrowing is stated here rather than
discovered in review.

## Outcome

`r2_size_alone` — the headline floor, log-size predictor.

## Predictors — fixed, and every one of them is design, not biology

Available in the committed table without recomputation:

| predictor | why it is design and not biology |
|---|---|
| `log10(n_hits)` | how many genes the screen called, a function of its threshold and power |
| `log10(n_measured)` | library size |
| `n_sets_used` | how many Hallmark sets cleared the ≥5-measured-members bar |
| `hit_rate = n_hits / n_measured` | the screen's calling rate |

**Excluded on purpose:** `cell_line`, `phenotype` and `library` are descriptive
curation, and a model that used them would be partly fitting BioGRID's
vocabulary rather than screen design. They are reported as a stratification
afterwards, never as model terms.

## Model — fixed

Ordinary least squares of `r2_size_alone` on the four predictors above, with an
intercept. No interactions, no transforms beyond those named, no variable
selection. **Evaluated by 5-fold cross-validated R², not in-sample R².** The
folds are assigned by `source_id`, so every screen from one publication lands in
the same fold — the corpus has one publication contributing 340 screens, and a
random split would let it appear on both sides and inflate the score. Seed
20260817, stated here.

## The claims, fixed before fitting

Let `Q` be the cross-validated R² of predicted floor against actual floor.

- **(a) The floor is largely a design artifact — `Q` ≥ 0.50.** More than half
  the variance in the no-biology floor is predictable from four numbers about
  how the screen was built, with no biology and no gene sets consulted. If (a)
  fires it is a general result about set-level statistics and is written as one,
  and it also sharpens scope limit 6 from a warning into a quantity.
- **(b) Partially predictable — 0.50 > `Q` ≥ 0.20.** Report the coefficient
  signs and the amount, and state that a floor cannot be replaced by a
  prediction of it.
- **(c) It does not generalise — `Q` < 0.20.** **Publish it.** This project has
  reported seven negative results out of eleven; a failed law is the next one,
  not a reason to keep fitting. No second model may be tried after seeing this
  value — the rule that makes the other ten evaluations worth anything.

## Controls

- **Permutation.** Shuffle the outcome 1,000 times, refit, and report the 95th
  percentile of `Q`. If the real `Q` does not clear it, nothing is claimed
  whatever branch fired. Seed 20260817.
- **Arithmetic sanity.** `hit_rate` is expected to dominate, because the corpus
  is entirely in the counting regime where the floor is partly arithmetic. That
  expectation is written down BEFORE fitting so that confirming it is not
  reported as a discovery.

## What this cannot show

- Nothing about mapping structures other than counting. The breadth arm's
  cross-domain question stays open and this arm does not close it.
- Nothing about whether any individual screen is good. A predictable floor is
  not a criticism of the screen that has one.
- Nothing gene-level, as everywhere else in this repository.

## Scope

Writes `results/floor_law/` only. Never `results/frozen/`. Post-hoc with respect
to the corpus, which already existed; pre-registered with respect to this model,
which does not yet.
