# Where this sits, and where it could go

Researched rather than reasoned from first principles. Sources are linked; where
I could not verify something I say so instead of filling the gap.

---

## 1. The problem has a price tag, and it is published

| Finding | Source |
|---|---|
| Cumulative prevalence of irreproducible preclinical research **exceeds 50%**, costing approximately **US$28 billion per year in the United States alone** | Freedman, Cockburn & Simcoe, *The Economics of Reproducibility in Preclinical Research*, PLOS Biology 13(6):e1002165, 2015. [doi:10.1371/journal.pbio.1002165](https://doi.org/10.1371/journal.pbio.1002165) |

That is the number the "run this before you commit a year to a hit" argument
rests on. It is a well-known figure and it is contested at the margins — the
estimate aggregates several categories of irreproducibility, not only false
leads from screens — but it is the standard citation and it is the right order
of magnitude.

## 2. The confound we measured is documented in adjacent fields

This matters more than it first looks. denali found that set-level rankings are
dominated by how the sets were built. **The same class of confound is published
in at least three other domains**, which means the finding is not a quirk of one
screen and the tool is not a one-dataset curiosity.

| Domain | The confound | Status |
|---|---|---|
| **Gene-set testing** | `VIF = 1 + (m−1)ρ̄` — set size × inter-gene correlation inflates competitive tests | **Solved in theory**, Wu & Smyth 2012 (CAMERA), [doi:10.1093/nar/gks461](https://doi.org/10.1093/nar/gks461). Our own post-freeze check recovered this empirically. |
| **RNA-seq enrichment** | Sample-specific **gene length bias** causes *"frequent false positive calls by gene-set enrichment analyses, leading to functional misinterpretation of the data"* | Published, [PLOS Biology 2019](https://journals.plos.org/plosbiology/article?id=10.1371/journal.pbio.3000481) |
| **GWAS gene-set analysis** | Gene size and LD structure bias gene-based tests | **Already corrected.** MAGMA regresses out SNV count, within-gene LD, minor-allele count and sample size. This vertical is closed. |
| **Single-cell differential expression** | Pseudoreplication produces *"a systematic excess of false positives compared to pseudobulk methods"* and *"a bias towards highly expressed genes"* | Squair et al., [Nature Communications 2021](https://www.nature.com/articles/s41467-021-25960-2) |

**Read that table honestly.** The confound is real and recurring, and in two of
four domains someone has already built the correction. That is not a reason to
stop; it is the reason our contribution is *measurement and disclosure* rather
than a new correction method. CAMERA tells you how to correct a test. It does
not tell a biologist holding a finished hit list how much of *their* ranking is
artifact, which is the question that costs money.

## 3. What we are not, stated plainly

We are not a target-discovery company and this repository should never imply
otherwise. Recursion, insitro and Cellarity generate their own data at scale and
sell candidate molecules. **We consume somebody else's finished screen and grade
it.** Different product, different customer, and much smaller.

We also could not verify, in the time available, whether any company has
commercialised a "which of your hits are artifacts" product specifically. Absence
of evidence here is weak evidence — I searched, I did not find one, and that is
all that can be claimed.

## 4. Where a next version would go, ranked by evidence of need

**1. Single-cell DE, as the strongest adjacent target.** The Squair result is the
closest analogue to ours in a much larger field: a widely-used statistical
approach producing systematic false positives with a size-and-expression bias,
published in Nature Communications, and still routinely ignored in practice. Our
`src/audit_screen.py` shape — take the table the analysis already produced,
report how much of it is explained by construction — transfers directly.

**2. RNA-seq enrichment, as the easiest.** The length-bias paper establishes the
need; the input is a standard enrichment results table. Lowest new-code cost of
anything here.

**3. Not GWAS.** MAGMA solved it. Building there would be re-solving a solved
problem, and someone would say so.

**4. Cross-screen concordance.** The question nobody in our search had answered
cleanly: how well do hit lists from independent screens of the same phenotype
agree? If that number is low and public, it is a stronger argument for this tool
than anything we currently cite. **We did not measure it and should not claim it.**

## 5. What this changes about the current project

Nothing about the result. It changes the framing:

- The finding is an instance of a **recurring class**, not a one-screen curiosity,
  and there is published precedent in three neighbouring fields.
- The right comparison is not "we found something new" — CAMERA got there in 2012
  — but **"we measured how much it costs you on a real genome-scale screen, and
  built the check as a tool anyone can run."**
- The $28B/year figure is the business case, and it belongs in the pitch rather
  than in a footnote.

---

**Method note.** Compiled 2026-08-15 from direct literature search. Four
automated research passes on the commercial landscape failed partway through for
unrelated infrastructure reasons, so the company section is thinner than the
methodology section and is marked as such. Everything above with a link was read;
everything without one is labelled as unverified.
