# Is it arithmetic or is it biology? Three domains that are not gene sets

**POST-HOC and EXPLORATORY. Nothing here was pre-registered.** Three domains were run,
three are reported. None was dropped, and the arm that came back weakest is reported at
the same size as the arm that came back strongest.

The question was whether denali's finding — that a set-level ranking is largely
predicted by how the sets were built — is a property of gene sets or a property of
arithmetic. Three domains with the same table shape were audited with the same
unmodified `audit()`: region sets, metabolite sets, and microbiome functional sets.

---

## The headline, and it is not the one this probe set out to find

**In all three domains `audit()` ran, returned large R² values, and those values do not
survive their own no-biology null.** The probe's most useful output is not a fourth
confirmation of the confound. It is a **boundary condition on the tool**, and it applies
to anyone running this check, including us.

`audit()` asks how much of a ranking is predicted by set size. That number is only
interpretable against what it would be **with no biology at all**, and the no-biology
value is not zero. It depends entirely on how `hits` was defined:

| structure | what `hits` counts | no-biology R² | correct null |
|---|---|---|---|
| **counting** | members of the set itself (`hits ≤ size`) | **large** | binomial at constant per-member rate |
| **no counting** | events over some other universe | ~0 | permutation |

Where hits are drawn from the set's own members — which is what classical overlap
enrichment does — regressing a count on the number of trials that produced it recovers
the trial count. **A high R² there is arithmetic, not a confound.** denali's own
off-target arm already caught and refused exactly this shape when a tautological
regression returned R² = 1.0000; this probe found the same trap one level further out,
and nearly walked into it.

`results/breadth/null_baselines.py` computes the correct null for every mapping.

## What each domain returned

Corpus percentile is against the 1,272-screen CRISPR distribution in `results/corpus/`.
**Read the null column before the percentile column.**

| domain | ran? | n | R² size alone | corpus percentile | its own null | verdict |
|---|---|---|---|---|---|---|
| **Region sets** (ChIP-Atlas) | yes | 87 jobs, 1.2M set-rows | **0.4035** median | 88th | control regions **0.5903** | **BELOW null** |
| **Metabolite sets** (SMPDB/KEGG × Metabolomics Workbench) | yes | 98–305 sets | **0.7935** (widest mapping) | 99th | binomial **0.8368** | **at/below null** |
| **Microbiome functional** (MetaCyc × 7 CRC cohorts) | yes | 409–471 pathways | **0.0019** (reaction-size) | 0.3rd | permutation **0.0023** | **INSIDE null** |
| — same domain, counting mapping | yes | 280–317 | 0.7956–0.8315 | 99th | binomial 0.77–0.81 | **at null** |
| *denali's own primary, for contrast* | — | 50 | *0.4649* | *90th* | permutation *0.0182* | ***ABOVE null*** |

**Region sets.** 94 real user-submitted ChIP-Atlas enrichment jobs; set = one ChIP-seq
experiment, size = peaks called, hits = query regions recovered, both read from the same
row of the same result file, so there is no join to get wrong. Real queries: median R²
0.4035. But each job ships its own **control** region set, randomised for most jobs and
containing no biology whatsoever — and those score **higher**: median 0.5903, control ≥
query in **82% of jobs**, paired median difference −0.128, Wilcoxon p = 1.3×10⁻⁹. The
matched noise floor is above the signal.

**Metabolite sets.** The brief predicted a boundary condition at small set sizes, and
there is one, though not the expected one. Sets are tiny (median 24 members, range
4–73). Across ~50 mappings and strata, the observed R² is **at or below the binomial
null in almost every one**. Restricting to sets under 20 members drops R² from 0.79 to
0.43 — but the null drops too, from 0.84 to 0.72, so the gap to the null does not open
up. The confound does not invert at small sizes so much as **never clear its baseline at
any size**.

**Microbiome functional sets.** The 67× size range is real — I confirmed it
independently: 987 MetaCyc pathways, 4 to 268 reactions, exactly 67.0×, against
Hallmark's 6.2×. But the median pathway has only **8** reactions, so that range is a long
tail, not a broad spread. With size = reaction count (the genuine construction quantity,
no counting structure), size explains **0.1–0.4% of the ranking** — the flattest result
anywhere in this project, sitting at the **0.3rd percentile** of the CRISPR corpus. The
same data mapped the counting way (size = members measured) returns 0.83, and that
number is its own null.

## The concordance arm, which is the part worth keeping

Domain (c) made denali's evaluation-6 question directly computable in a second field:
**21 cohort pairs** across 7 independent CRC metagenomic cohorts, asking how much
cross-cohort replication is pathway size.

| mapping | median raw agreement | after removing size | share that is size |
|---|---|---|---|
| reaction-count size (no counting structure) | 0.87–0.98 | 0.86–0.98 | **−1.6% to +1.6%** |
| members-measured (counting structure) | 0.77 | 0.36 | 53.5% |
| *denali's own two CRISPR screens* | *0.663* | *0.493* | *26%* |

**With the honest construction quantity, essentially none of the cross-cohort agreement
is pathway size.** Microbiome pathway replication across cohorts is not carried by how
big the pathways are. The 53.5% figure in the counting mapping is the arithmetic again,
not a second confirmation.

## What this says about denali's own numbers

Reported here because the probe produced it and it points inward.

- **The published primary (0.4649) survives.** Its `hits` counts *perturbations* — up to
  5,707, against a maximum set size of 194 — so it has no counting structure and takes a
  permutation null. Observed 0.4649 against a null of **0.0182 [0.000, 0.098]**:
  decisively above. This is the only arm in this entire probe that clears its null.
- **The corpus arm (evaluation 10) has the counting structure and has never been shown
  against it.** `src/corpus_audit.py` sets hits = set members that were hits, so
  `hits ≤ size` in every screen. On a 250-screen sample of the same substrate under the
  same inclusion rule, observed median R² is **0.19** against a binomial null median of
  **0.79**, with the observed above its own null in only **6%** of screens. The published
  statement that "in a typical published screen, roughly a fifth of the ranking is
  predicted by set size" remains **arithmetically true as a descriptive share**, and
  nothing in `results/corpus/` is wrong. But it should not be read as *size inflating*
  those rankings, because the no-biology baseline is far higher, not lower. **That
  interpretation is not corrected here** — evaluation 10 is published across several
  surfaces, and changing how it reads is a decision for the author, not a side effect of
  an exploratory probe.

## Prior art, which shrinks the contribution

The distinctive move — score the outcome using only the construction quantity and report
what fraction it recovers — **is not new**, and the writeup must not claim it is.

- Gillis J, Pavlidis P. *The impact of multifunctional genes on "guilt by association"
  analysis.* PLoS ONE 2011;6(2):e17258. [doi:10.1371/journal.pone.0017258](https://doi.org/10.1371/journal.pone.0017258)
- Ballouz S, Weber M, Pavlidis P, Gillis J. *EGAD: ultra-fast functional analysis of gene
  networks.* Bioinformatics 2017;33(4):612–614. [doi:10.1093/bioinformatics/btw695](https://doi.org/10.1093/bioinformatics/btw695)
  — ships **node-degree AUROC as a routine built-in null**, i.e. this diagnostic packaged
  as software since 2017.
- Crow M, Lim N, Ballouz S, Pavlidis P, Gillis J. *Predictability of human differential
  gene expression.* PNAS 2019;116(13):6491–6500. [doi:10.1073/pnas.1802973116](https://doi.org/10.1073/pnas.1802973116)
  — the cross-dataset version of the estimand, at a magnitude well above denali's 26%.

Region sets in particular are **already corrected in standard practice**: GREAT (McLean
et al., *Nat Biotechnol* 2010, [doi:10.1038/nbt.1630](https://doi.org/10.1038/nbt.1630))
exists *because* the naive test is biased by regulatory-domain size; ChIP-Enrich, LOLA's
region universe, regioneR permutation nulls and `bedtools fisher` all address it. **There
is no methodological gap to claim in that domain.**

What survives: this diagnostic is standard in one subfield and had not been carried
across to region-set, metabolite-set or microbiome-functional enrichment — and when it
is carried across, **the answer in all three is that the size relationship is the
counting arithmetic, not an additional confound.**

## What would make this wrong

- **The nulls are constant-rate.** A real per-member hit rate that varies with size for
  biological reasons would change the baseline. The binomial is the simplest defensible
  null, not the only one.
- **The region control sets are the tool's own controls**, randomised for most but not
  all jobs; the 18% that are not randomised weaken that arm's null.
- **Estimand mismatch with the corpus percentile.** The corpus column uses a log-size
  predictor; several mappings here use raw size. The percentiles are indicative, not
  exact, and are reported that way.
- **Coverage mappings are not differential-abundance mappings.** Several metabolite and
  microbiome arms ask "how many members were measurable", which is the annotation
  coverage question, not the hit-list question. Labelled per arm.
- Selection into public repositories is not random in any of the three domains.

## Scope

Collection-level and distribution-level statistics only. **No experiment, antigen, cell
type, genomic region, metabolite, compound, pathway, species or gene is named as a
finding, as confounded, or as a candidate anywhere in this directory.** The unit of
inference is the distribution. No clinical or wet-lab recommendation follows.

## Reproduce

```bash
python results/breadth/null_baselines.py      # the null column, from committed tables
```

Per-domain provenance, URLs, byte counts and assumptions are in each subdirectory's
`README.md`. The 107 MB of raw ChIP-Atlas job results and the 1.2M-row set-level table
derived from them are **gitignored and re-fetchable**, exactly as `data/raw/` is
handled; the committed `regions/per_job_r2.csv` is what every region number above is
computed from.
