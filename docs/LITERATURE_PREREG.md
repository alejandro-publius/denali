# Pre-registration — evaluation 11, the literature audit

**Written and committed before the audit was run.** Nothing below was chosen
after seeing a value. The only thing known at the time of writing is that PMID
resolution works at all: two PMIDs were resolved as a feasibility spike, one hit
and one missed, which establishes that coverage is partial without revealing
anything about the outcome.

Verify this file predates the result by comparing its commit to the commit that
adds `results/literature/`.

## The question

The corpus arm (evaluation 10) measured the size confound across **1,272
published screens drawn from 187 publications** and found a field median of
**0.224**. It did not ask whether the field *knows*. This arm asks exactly that:

> Of the publications behind those screens, what fraction discuss gene-set size,
> or set-level statistical confounding, anywhere in their full text?

A confound that the literature already discusses is a known limitation. One it
does not is an unacknowledged one, and those are different claims about the same
number.

## Why this is worth running at all

The corpus arm's honest weakness is that it measures screens rather than
scientists. A screen cannot know it is confounded; a paper can say so. This is
the closest available check on whether our finding is news.

## Substrate

- **Query set:** the 187 unique `source_id` values in
  `results/corpus/corpus_per_screen.csv`. This set is **disjoint from the 20
  probe genes in FIG 4**, so running it cannot move any number that figure
  reports.
- **Index:** Paperclip, sources PubMed Central / bioRxiv / medRxiv / arXiv.
  Open-access full text only.

## Search terms — FIXED HERE, BEFORE ANY RUN

Two tiers, both applied to full document text, case-insensitive.

**Tier A — explicit size discussion.** The paper names set size as a factor.

```
gene[- ]set size | pathway size | set size | size bias | size[- ]dependent
larger gene sets | number of genes in the (gene )?set | set[- ]size
```

**Tier B — competitive-test awareness.** The paper does not necessarily say
"size" but uses or cites machinery that exists because of this confound.

```
CAMERA | competitive (gene set )?test | self[- ]contained test
inter[- ]gene correlation | variance inflation
```

A publication counts for a tier if **any** term in that tier matches anywhere in
its full text. Tiers are reported separately and also as a union. A match is
evidence the topic is *mentioned*, not that it is handled correctly — that
distinction is stated in the result and is not something a regex can settle.

## Power rule — fires before any number is interpreted

**If fewer than 60 of the 187 publications resolve to full text, this arm issues
NO VERDICT** and the fractions below carry none. Sixty is 32% of the query set
and is chosen as the point below which a fraction over the resolved subset says
more about PubMed Central's coverage than about the field.

This is the same rule shape that fired against us in evaluations 3 and 7. It is
written here so it can fire again.

## The pre-registered claim

> **(a)** If Tier A ≥ 50% of resolved publications, the field discusses set size
> and our "unacknowledged" framing is **wrong**. We report that, and the corpus
> arm becomes a quantification of a known problem rather than a new one.
>
> **(b)** If Tier A < 50%, the majority of the publications whose screens we
> audited do not mention set size, and that becomes the reported finding.

Both branches are publishable. **(a)** costs us the more interesting story,
which is why it is written down first.

## What would change my mind

- **Resolution below 60** → no verdict, regardless of how the fractions look.
- **Tier A ≥ 50%** → claim (a) fires; the framing changes, not the number.
- **A near-total Tier B hit rate** would suggest the regex is matching boilerplate
  methods citations rather than engagement. If Tier B exceeds 90%, we report
  Tier B as uninformative rather than as agreement.

## Scope limits

- **Aggregate counts only. No publication is named**, in this document, in the
  result, or on any rendered surface. An existing invariant already fails the
  build if a PMID or screen id appears in the corpus surfaces, and this arm
  inherits it.
- **This is a keyword audit, not a reading.** It measures mention, not
  understanding. Saying otherwise would be the same overreach this project keeps
  finding in other people's work.
- **PMC open access is not the literature.** Every fraction is a fraction of what
  resolved, and the denominator is reported next to it every time.
- This arm does not revise the pre-registered K562 primary in `results/frozen/`,
  and writes only to `results/literature/`.

## Labelling

**PRE-REGISTERED** as to its claim, power rule and search terms. The *arm itself*
is post-freeze — it was built after the primary analysis closed — and it says so
wherever it appears, exactly as evaluations 6, 8 and 10 do.
