# Six domains, one recipe: is it arithmetic?

**Pre-registered** in `docs/DOMAINS_PREREG.md` (`6d40a079…`, commit `a2776f7`),
written and hashed **before any domain substrate was downloaded**; correction 1
appended at `8d2296a`, before any domain-5 value existed. Post-deadline
extension work; `results/frozen/` and `results/corpus/` untouched. All numbers:
`results/domains/`.

---

## The negatives first

Two of the six domains' **registered hit rules produced degenerate numbers**,
and in both cases the degenerate number was the flattering one.

- **Proteins.** The registered rule (BH q < 0.05) makes **75%** of measured
  proteins hits. The pre-registered hit-fraction guard fired on its own and
  required the stricter variant. The degenerate primary was R² = 0.697; the
  usable number is **0.371**.
- **Metabolites.** The registered rule makes **86%** of metabolites hits. At
  that rate, member hits ≈ 0.86 × set size as an *arithmetic identity*, and the
  resulting R² of 0.913 measures a tautology. No guard was registered for this
  domain — that is our omission, not a discovery — so the strict-hit variant is
  labelled **post-hoc** and the degenerate primary is printed beside it.

A third: **six of eleven microbiome cohorts return no significant stratum at
all** under the registered rule. Their size-alone R² does not exist. They are
counted as UNSCOREABLE, never scored — reporting them as "not size-dominated"
would have been precisely the error this project exists to catch.

## The table

| domain | sets | size range | R² size alone (raw) | R² (log) | verdict | percentile vs 1,272 CRISPR screens | top-10 survive |
|---|---:|---|---:|---:|---|---:|---:|
| 1 · gene sets (CRISPR screens) | 50/screen | varies | 0.192 | 0.224 | reference distribution | 50 | — |
| 6 · **yeast genetic interaction** | 117 | 7–1,377 | 0.357 | 0.681 | PARTIALLY CONFOUNDED | **96.1** | 5/10 |
| 2 · region sets | 300 | 15–84,580 | 0.648 | 0.893 | **CONFOUNDED** | **99.6** | 0/10 |
| 3 · metabolite sets *(boundary)* | 91 | 3–8 | 0.331 | 0.299 | PARTIALLY CONFOUNDED | 81.8 | 10/10 |
| 4 · protein sets | 1,277 | 5–399 | 0.371 | 0.431 | PARTIALLY CONFOUNDED | 89.2 | 1/10 |
| 5 · microbiome functions | 5 cohorts | 5–570 | 0.633 | 0.446 | **CONFOUNDED** (4/5) | 89.7 | 1/10 |

Rows 3 and 4 carry the non-degenerate variant; row 1 is the reference
distribution the others are placed against, so its percentile is 50 by
construction. Raw and log columns are different transforms of the same data
and are never compared to each other — percentiles use log against log.

**Pre-registered claim (a) is supported**: 6 of 6 rows defensible (threshold
≥ 4), 5 reaching the PARTIAL line (≥ 3), and 2 non-gene domains reaching
CONFOUNDED (≥ 1).

## Domain 6 kills the strongest objection

The strongest argument against this project has always been: *the confound is
an artifact of sloppy human curation — annotate carefully and it goes away.*

*Saccharomyces cerevisiae* is the best-annotated organism in biology. We took
the Costanzo 2016 global genetic interaction network — **15.8 million measured
gene pairs** across three datasets — scored each of 5,292 genes by its count of
significant negative interactions at the study's own intermediate stringency,
called the top 10% hits, and audited SGD's curated GO Slim.

**It sits at the 96th percentile of the published CRISPR corpus.** The
pre-registered expectation was "at or above the 25th percentile"; the
alternative — below the 10th, meaning annotation quality rescues set-level
inference — is decisively rejected. Decades of expert curation do not remove
the confound. Five of the top ten GO Slim terms leave the top ten once size is
accounted for.

## Domain 2 is the cleanest demonstration in the project

Region sets share **nothing** with gene-set machinery: no gene symbols, no
annotation database, no curation, no biologist's judgement about what belongs
together. A "set" is a pile of genomic intervals a ChIP experiment called, and
its size is a property of antibody, sequencing depth and peak caller.

300 ChIP-Atlas experiments, sizes from 15 to 84,580 peaks — a **5,639-fold**
range — against genome-wide significant SNPs for the trait with the most
catalogued associations. Size alone explains **89%** of the log-scale ranking,
the 99.6th percentile, and **not one** of the top ten survives re-ranking.

An experiment that calls more peaks covers more genome and therefore overlaps
more query SNPs. That is not biology under any description. It is area.

The trait and the cell-type class were selected by independent deterministic
rules, so this is **not** a tissue-matched analysis and nothing here is a
biological claim about either. Set sizes were counted from the downloaded peak
files, not taken from metadata; the two agree on **300 of 300**.

## Domain 3 answers the boundary question, in an unexpected way

Metabolite sets are 3–8 members — the regime where the confound might need
large sets to appear. At a sane hit rate it is still there: **R² = 0.331**,
81.8th percentile. But **all ten** of the top ten survive re-ranking, because
with six hits spread over 91 sets the top of the list is almost entirely ties.

So the boundary condition failed in the opposite direction from the one
anticipated. The problem is not that small sets are immune; it is that a
63-compound assay **cannot define a meaningful null** against sets of 3–8
members. The confound is present and the ranking is not resolvable enough for
it to matter.

## Domain 5 carries the concordance arm

Eleven CRC cohorts, of which five are scoreable. Among those, four of five are
CONFOUNDED, median R² 0.633, and the median cohort keeps **one** of its top
ten after re-ranking.

Because there are multiple cohorts this domain answers denali's evaluation-6
question directly: **when two independent cohorts agree, how much of the
agreement is set size?** Across all ten pairs, the median is **28%** —
close to the 26% measured between the two CRISPR cell lines in the original
work, in a field that shares no organism, assay or annotation with it.

**This is a deviation.** The registered set definition (MetaCyc
superpathway/ontology classes) is not publicly obtainable — HUMAnN's public
file expands superpathways to reactions and MetaCyc's hierarchy is
license-gated. The substitute (sets = pathways, members = the species carrying
them) was fixed in correction 1 at `8d2296a`, **before any domain-5 value
existed**, and is labelled wherever it is reported.

## What the table does not say

- **A high R² does not mean any particular set is wrong**, and driving one to
  zero would not prove a ranking correct.
- **The hit rules are ours.** Each is a published-style default, and where a
  domain's registered rule was degenerate the variant is labelled and the
  original printed beside it. None was chosen after seeing its number.
- **No individual set, experiment, cohort, trait, species or publication is
  named as a finding.** The unit of inference is the distribution.
- The percentile column places each domain against a CRISPR corpus whose own
  construction is documented, and whose median is not "the field's value" —
  see `docs/CORPUS.md`, including the independent run that disagreed.
- These are six constructions, not six fields. Another defensible construction
  in the same domain could land elsewhere; the claim is about whether the
  effect appears at all outside gene sets, and it does.

## Reproduce

```bash
.venv/bin/python -m src.domain_yeast        # Costanzo 2016 + SGD GO Slim
.venv/bin/python -m src.domain_regions      # ChIP-Atlas + GWAS Catalog
.venv/bin/python -m src.domain_metabolite   # MetaboAnalyst + SMPDB
.venv/bin/python -m src.domain_protein      # CPTAC + Reactome
Rscript src/microbiome_extract.R            # curatedMetagenomicData 3.20.0
.venv/bin/python -m src.domain_microbiome
.venv/bin/python -m src.domains_table       # assembles, recomputes nothing
```

Every substrate is a public download without authentication. Each module's
docstring names its source, its construction and any implementation decision
fixed before a value was computed.
