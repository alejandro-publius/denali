# Where this sits, and where it could go

Researched rather than reasoned from first principles. Sources are linked; where
I could not verify something I say so instead of filling the gap.

---

## 0. The field just named our problem as *the* bottleneck

This is the most important thing in this document and it was published a month
before the event.

Google DeepMind, *Conjecture Machines: AI agents and the new validation
bottleneck in science*, July 2026:

> **"The bottleneck for AI for Science is no longer hypothesis generation, it is
> verification.** Karl Popper said science advances through conjectures and
> refutations. Agentic AI is changing the economics of that pairing. AI agents
> are conjecture machines, making ideas and candidate solutions abundant and
> relatively cheap. Refutations remain physical and institutional — and so,
> costly and slow."

And the failure mode they name:

> "An agent can propose a novel genetic lead to reverse cellular ageing, but
> cannot say definitively whether it actually works."

They list **calibrating confidence about what the agent does not know** — the
"epistemic humility" problem — as an open weakness of current systems.

**Read the field against that.** Lila Sciences runs autonomous science factories
that hypothesise and iterate without human guidance. FutureHouse's Kosmos and
Robin generate thousands of candidate hypotheses in a single run. Google's own
Co-Scientist proposes testable experiments *"at a rate no laboratory can fully
evaluate."* Every one of them is a conjecture machine, and they are collectively
making the bottleneck worse.

**denali is a refutation machine.** It does not propose candidates — it refuses
to, on the record, and the pre-registration is what forbids it. What it does is
take a ranked list somebody already believes and measure how much of it is
artifact. On its own held-out test it reported its own predictor failing at
balanced accuracy 0.4375 with zero true positives, unasked. That is the epistemic
humility DeepMind names as missing, implemented rather than aspired to.

This is not a smaller version of an AI scientist. **It is the other half**, and
the half the field's leading policy voice says is now the constraint.

Corroborating that this is a live front, not one company's opinion:
NeurIPS 2026 has a workshop titled *Verification in the Age of AI Scientists*,
and Philosophical Transactions of the Royal Society A published *The need for
verification in artificial intelligence-driven scientific discovery*. DeepMind
has gone as far as building a wet lab inside the Francis Crick Institute
specifically to validate agent hypotheses — which is what it costs to refute
things physically, and why doing it computationally first has value.

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

**4. Cross-screen concordance — since answered, by us.** This section previously
said *"we did not measure it and should not claim it."* We then measured it on our
own two screens: raw agreement ρ +0.663, ρ +0.493 after removing set size, so 26%
of the apparent replication is carried by set size, and **6 of the top 10 programs
in an independent cell line are predictable from set size alone**. Post-freeze,
not pre-registered, and a measurement on two screens rather than a general
estimate. See `results/concordance/`.

**5. Annotation coverage — a question we did not know to ask.** Also since
measured, and it is the one finding here we have not seen stated anywhere: **98%
of Hallmark sets can be scored against a genome-scale screen; 46% of GO Biological
Process sets can.** The median GO-BP set declares 20 genes and has 8 measured in
this screen. If more than half of the most-used gene-set collection in biology
cannot be evaluated against a screen at all, that is a coverage problem sitting
underneath every enrichment result computed on it — and it is upstream of the
size confound rather than a version of it. Descriptive, not pre-registered; the
arm it came from failed its own power rule. See `results/annotation/`.

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

## 6. Time-sensitive: Virtual Cell Challenge 2026 opens 20 August

Arc Institute — a co-host of this event — opens round two of the Virtual Cell
Challenge on **Thursday 20 August 2026**, four days after this hackathon ends.
Announced scope: *"a new problem to solve and a wider scope"*; the 2025 wrap-up
signals expansion toward **combinatorial perturbations and cross-cell-type
generalization**. Round one drew 5,000+ registrants across 114 countries and 300+
final submissions.

Two things from their own 2025 post-mortem are worth reading as an invitation:

> *"purely AI-based approaches did not consistently outperform statistical
> baselines"*

> *"no single metric captures model quality"*

Both are this project's argument, in their words. The cross-cell-type direction is
also exactly what our RPE1 arm just tested. **This is the obvious next venue**, and
unlike a hackathon it rewards a method that holds up rather than a demo.

**Method note.** Compiled 2026-08-15 from direct literature search. Four
automated research passes on the commercial landscape failed partway through for
unrelated infrastructure reasons, so the company section is thinner than the
methodology section and is marked as such. Everything above with a link was read;
everything without one is labelled as unverified.
