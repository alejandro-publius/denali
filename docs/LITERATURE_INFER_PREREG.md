# Pre-registration — evaluation 12, the literature arm read rather than grepped

**Sealed before any paper was classified.** Hash this file, commit it, then run
`src/literature_infer.py`. Nothing below may be edited after a label exists. A
deviation is appended underneath as a correction, never folded into the text
above, following `docs/LITERATURE_PREREG.md`.

## Why this arm exists

Evaluation 11 classified 111 publications with `grep -i -c -e` over eight Tier A
patterns and five Tier B patterns. Its own output says what that buys:

> A regex match is evidence a topic is MENTIONED, not that it is handled
> correctly. This measures mention, not understanding, and claiming otherwise
> would be the overreach this project exists to detect.

That stated limitation is the thing this arm tests. A regex can fail in two
directions and evaluation 11 can distinguish neither:

- **Overcount.** The pattern fires on a passing phrase, a figure caption, or a
  LaTeX preamble, and the paper does nothing about set size. Already observed:
  the Tier A term `pathway size` matches `PMC7373179` inside a block of
  `\usepackage` directives.
- **Undercount.** The paper handles set size properly in words none of the
  thirteen patterns contain — "we permuted within size strata", "background
  matched on the number of annotated genes", "normalised enrichment score" —
  and is scored as silent.

The second direction is the one that matters to this project's framing, and it
is the one a regex structurally cannot see.

## The question

Of the publications behind the corpus arm's 1,272 screens, what fraction did
anything about gene-set size, as judged by a model reading the full text rather
than by pattern match?

## Population and denominator

The **111 publications of 187** that evaluation 11 resolved to full text in
PubMed Central, unchanged and not re-resolved. Using the same denominator is the
point: any difference between the two arms is then attributable to the reading
method and not to a different sample.

Every fraction reported is a fraction of those 111. Open access is not a random
sample of publishing and the resolution rate of 59.4% is carried into every
statement, exactly as evaluation 11 carries it.

## The label set — fixed here, and the only values accepted

Exactly one label per publication. Structured output is constrained to this set
and anything else is a failed paper, not a coerced one.

| label | means |
|---|---|
| `NONE` | Nothing about set size, set construction, or the statistical consequences of either. |
| `MENTIONS` | Refers to it and does nothing about it. Includes noting it as a limitation. |
| `ADJUSTS` | Uses a method that accounts for it — a competitive test, a permutation preserving set size, a size-matched background or gene universe, normalisation by set size. The paper need not name the confound. |
| `MEASURES` | Quantifies the effect of set size on its own results: a correlation, an R², a null distribution, a sensitivity analysis, a size-stratified comparison. |

`ADJUSTS` and `MEASURES` both require the paper to have **done** something.
`MENTIONS` is the label for knowing and not acting. The primary quantity is
deliberately the fraction that acted.

## Primary quantity

**`ACTED` = the share of the 111 labelled `ADJUSTS` or `MEASURES`.**

## The claims, and which way each cuts

Stated before the value exists, with the direction that would hurt us named
first because that is the one worth pre-committing to.

- **(a) Our framing is materially wrong — `ACTED` ≥ 25%.** A quarter of the
  field handling set size means "the field does not check this" is false as
  stated. If (a) fires it goes in `README.md` at the same size as every other
  headline, and the novelty claim for this project is reduced in the same edit.
  It is not a footnote and it is not deferred to a limitations section.
- **(b) The regex undercounted but the picture holds — 18.0% > `ACTED` ≥ 8%.**
  Report the corrected figure with the gap and the direction stated.
- **(c) The regex was roughly right — `ACTED` < 8%.** Report both and note that
  two methods agreeing is weak evidence when one of them was built to be
  conservative.

The comparison figure from evaluation 11 is its **union of either tier, 20 of
111 = 18.0%**, which is the closest thing that arm has to "engaged with the
topic". Its Tier A alone is 4 of 111 = 3.6%. Both are restated beside the model
figure and neither is dropped for being inconvenient.

## Two passes, and how disagreement is handled

Every publication is classified once by the **primary** model. **Every paper the
primary labels `ADJUSTS` or `MEASURES` is re-read independently by a second,
different model**, blind to the first label.

Disagreement is **reported as a band and never averaged, never broken by a
third vote, and never resolved by the author**:

- **lower bound** = papers both models put in `ACTED`
- **upper bound** = papers either model puts in `ACTED`

If the band is wider than 10 percentage points, the arm reports the band and
declines to state a point estimate at all. A single number extracted from two
disagreeing readers would be the false precision this project exists to detect.

Only `ACTED` positives get a second pass. That is a stated asymmetry and it
bounds the result in one direction: a paper the primary wrongly labelled `NONE`
is never rescued, so **the lower bound is a genuine lower bound and the upper
bound is not a genuine upper bound.** Said here rather than discovered later.

## Controls, fixed before the run

- **Positive.** `PMC7373179`, `PMC5336655`, `PMC2661051` — three gene-set
  enrichment *methods* papers, the same three evaluation 11 used. All three must
  come back `ADJUSTS` or `MEASURES`. Fewer than three and the classifier is not
  measuring what this arm claims, and the arm reports as broken rather than
  reporting a number.
- **Negative.** The primary must not label the whole population `ACTED`. If
  `ACTED` exceeds 90% the classifier is agreeing with the prompt rather than
  reading, and the arm reports as uninformative — the same shape as evaluation
  11's Tier B ceiling.

## Power

No power rule applies: the population is fixed at 111 and enumerated, not
sampled. A publication whose full text cannot be retrieved at run time is
reported as `UNRETRIEVED` and removed from the denominator, with the count
stated. If more than 20 of 111 go unretrieved the arm reports as underpowered
against evaluation 11, because the two denominators would no longer be the same
sample and the comparison would be between arms rather than between methods.

## Scope

- Writes `results/literature_infer/` **only**. It must never write
  `results/frozen/`. No headline in this repository changes because a language
  model said so.
- Aggregate counts only. No publication is named on any rendered surface; the
  existing scope invariant already fails the build if a PMID appears there.
- This is an **ESTIMATE produced by a language model reading text**, and a dated
  observation against a live index, exactly as evaluations 11 and the retrieval
  probe are. It is deliberately not a `make all` step and its numbers are not
  reproducible by re-running — they are reproducible from the committed cache.
- **This arm cannot establish that a paper's adjustment was correct**, only that
  it was made. That is the same class of limitation as evaluation 11's, moved
  one step out, and it is not fixed by this arm.

## Caching

Every model response is cached by the sha256 of (document id, prompt, model,
schema). A rerun costs nothing and returns the identical labels. The cache is
committed, so the aggregate is recomputable by anyone without an API key and
without the index.

---

# CORRECTION 1 — appended 2026-08-17, before any label was computed

Written after the pre-registration above was sealed at sha256 `cd8252ff…`
(commit `ae63e18`) and before a single paper was classified. Appended rather
than folded in, per this project's rule.

**What changed.** The pre-registration says the model reads "the full text". It
cannot, for two reasons discovered while wiring the run and neither of them
known when the text above was sealed:

1. `paperclip map`, the index's own parallel LLM reader — the mechanism this arm
   was designed around, and the one that supports `--output-schema` and a
   `--model` override natively — returns
   `Parallel map workers are currently limited to GXL testers` on this account.
2. `paperclip cat` truncates every file at approximately 1,000 characters,
   including individual `sections/*.lines` files. A paper is roughly 37,000
   tokens and there is no flag to read it whole.

**What is done instead.** Each publication is classified from **context windows
returned by `paperclip scan` over a deliberately broad recall pattern set of 25
terms**, rather than from the whole document. The pattern set is recorded in
`results/literature_infer/patterns.json` and is far wider than evaluation 11's
thirteen, by design: it covers method language that never says "size" —
`competitive`, `self-contained`, `permutation`, `null distribution`,
`background set`, `gene universe`, `normalised enrichment score`,
`hypergeometric`, `over-representation`, `size-matched`, `stratified by size`
and others. `scan` returns each match with surrounding lines, so the classifier
sees the passage rather than the term.

**What this costs, stated plainly.** The classifier's recall is now bounded by
the pattern set. A paper that adjusts for set size using language none of the 25
terms touches is still invisible, exactly as it was to evaluation 11 — the
window is much wider, and it is still a window. **The undercount direction is
therefore reduced but not eliminated, and this arm cannot claim to have removed
it.** The overcount direction is fully addressed, because every match is read in
context and a hit inside a LaTeX preamble or a reference list is now judged as
`NONE` rather than counted.

This weakens the arm against its own stated purpose and is reported here rather
than in the results, where it would read as a caveat on a number instead of a
limit on the method.

**Unchanged:** the population of 111, the four labels, the primary quantity, all
three claims and their thresholds, the 25% kill criterion, the two-model second
pass, the band rule, both controls, and the scope restrictions. No threshold
moved.
