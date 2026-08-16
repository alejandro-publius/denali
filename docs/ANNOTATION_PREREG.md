# Annotation-scaling arm — pre-registration

**Written and committed before the sweep was run.** No threshold below was chosen
after seeing a value.

---

## The question

Everything this project has measured used **MSigDB Hallmark**: 50 sets,
hand-curated, spanning 32–200 genes. That is the *cleanest* annotation in common
use. Almost nobody analyses screens with Hallmark alone — they use Reactome, or
GO Biological Process, which is the most-used gene-set collection in biology.

Those collections are much larger and much less uniform:

| Collection | Sets | Size range | Curation |
|---|--:|---|---|
| Hallmark | 50 | 32–200 (**6×**) | hand-curated, deliberately uniform |
| WikiPathways | 925 | 5–507 (**101×**) | community-curated |
| Reactome | 1,839 | 5–1,497 (**299×**) | expert hierarchy, nested sets |
| GO Biological Process | 7,538 | 5–1,988 (**398×**) | largely automated, deeply nested |

If apparent reversibility is driven by set size, then **the confound should get
worse as the size range widens** — and the collection most biologists actually
use should be the worst affected. That is a testable prediction and it has not
been made in this project before.

## Primary claim

**(a)** The share of variance explained by set size alone increases
monotonically with the collection's size range. Concretely: GO-BP and Reactome
each show a **higher** size-alone R² than Hallmark's 0.4649.

## Alternative claim

**(b)** It does not. The size effect is flat or lower in the larger collections,
which would mean Hallmark's uniformity is not what limits the confound and our
generalisation from it is weaker than we thought. We would report that.

## Deciding statistic, fixed now

Per collection: `R²` of `R_p` on `n_present` alone, OLS, one predictor, over the
sets sampled from that collection. `R_p = log10(1 + hits at q<0.05)`, BH within
set. **The byte-frozen scorer `src/score_k562.py` (sha256 `2abfdc6f…`) is used
unmodified.**

| Outcome | Threshold | Verdict |
|---|---|---|
| Claim (a) | GO-BP R² ≥ 0.4649 **and** Reactome R² ≥ 0.4649 | Confound worsens with looser annotation |
| Partial | exactly one of the two clears Hallmark | **PARTIAL** — reported, not spun |
| Claim (b) | neither clears Hallmark | Does not scale with annotation looseness |

Reported alongside, with no threshold attached and no interpretation applied
after the fact: the same figure for WikiPathways, and Spearman ρ between a
collection's size range and its R².

## Sampling, fixed now

Scoring all 10,352 sets is ~28 CPU-hours. We sample **250 sets per collection**,
drawn with `numpy.random.default_rng(20260815)` — the seed used everywhere else
in this project — **stratified across size deciles** so the sample spans each
collection's range rather than clustering at its mode. Hallmark is used in full
(all 50). The sample is drawn **before** any set is scored.

## What would make us report neither

If fewer than **150 of 250** sets in any collection are scoreable, that
collection is reported as **UNDERPOWERED** and contributes no verdict — the same
rule that fired against us on the held-out ten.

## Constraints

1. `results/frozen/` is not touched. Output goes to `results/annotation/`.
2. The K562 headline is not revised by this arm. It broadens or narrows the
   *scope* of the claim, nothing else.
3. No gene-level claim, in any collection.
4. **No set is named as a finding.** A collection-level statistic is the unit;
   naming the "most confounded pathway" would be the nomination this project
   refuses to make.
5. Nested sets are a real feature of Reactome and GO, not a defect to correct —
   parent and child sets overlap, and that overlap is part of what we are
   measuring. It is disclosed, not adjusted away.
