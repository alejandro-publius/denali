# Pre-registration — does the verdict depend on who called the hits?

**Evaluation 14. Committed before any value it decides.** Written 2026-08-17 in an
isolated clone at `1010d4d`. Post-hoc with respect to the frozen matrix, which
already existed; pre-registered with respect to every number below, none of which
had been computed when this file was sealed.

Nothing here writes `results/frozen/`. No gene, gene set or publication is named
as a finding.

---

## 0 · Why this arm exists, and what it is not

`denali audit` takes a table of set sizes and hit counts and reports what share
of the ranking is predicted by set construction. It has never asked **where the
hit column came from.**

Every hit count in this project was produced by one convention: a two-sided
normal p-value on the reversal statistic, Benjamini–Hochberg corrected within
each program, thresholded at q < 0.05. That convention was fixed in
`src/sweep.py` before the sweep and never varied. So the published 0.4649 is a
statement about *this screen scored this way*, and the project has no evidence
about what happens under any other way.

This matters because the mechanism the project attributes the confound to is
**statistical power**: a program with more measured members yields a more precise
rank statistic, so more of its perturbations clear a fixed threshold. That
mechanism is a property of *thresholding*. A hit rule that does not threshold —
one that takes the top q% or the top N per set — cannot express it in the hit
count at all, because the hit count is then fixed by the rule rather than by the
data.

If that is right, the tool's verdict is partly a function of the caller's
convention rather than of the caller's biology, and the tool says nothing about
it on its output. That would be a defect in a shipped instrument, not a curiosity.

**This is not a claim that any convention is wrong.** Thresholding and
quantile-cutting are both standard and both defensible. The question is only
whether denali's answer changes between them, and whether it admits that.

## 1 · The question

Holding the underlying screen completely fixed, does denali's verdict change when
only the hit-calling rule changes?

## 2 · The substrate, fixed before running

`results/frozen/matrix.csv` — the frozen reversal statistic `u_z` for 9,837
target genes across 50 MSigDB Hallmark programs. Read-only. Non-finite entries
are **masked, never imputed**, per `CLAUDE.md`.

Set size is `n_present` from `results/frozen/program_summary.csv`, unchanged, so
the size column is identical across all rules and only the hit column moves.

**A disclosed substrate gap, written down before it can be discovered.**
`matrix.csv` is not the vector the published hit counts were computed on.
`src/sweep.py` counts hits over all 11,258 perturbation rows and only then
collapses to 9,837 unique target genes by taking each gene's **maximum** `u_z`.
Recomputing any threshold rule on the collapsed matrix therefore cannot reproduce
`n_hits_q05`: there are fewer rows, the max-collapse shifts the distribution
upward, and the Benjamini–Hochberg denominator differs. The 470 MB substrate that
would allow the uncollapsed comparison is gitignored and absent.

Consequence, fixed now: **every absolute R² in this arm is substrate-specific and
is not comparable to the published 0.4649.** The comparison this arm is entitled
to make is *across rules on one substrate*, which is exactly the comparison the
question needs. No number from this arm may be quoted as the project's headline,
and none may revise it.

## 3 · The rules, fixed before running

Seven, chosen to span the two families and committed here in full. Three
threshold rules, three rules that fix the count by construction, and one fixed
effect-size cut that sits between them.

| # | rule | family |
|---|---|---|
| R1 | BH-corrected q < 0.05 within program — **the published convention** | threshold |
| R2 | uncorrected two-sided p < 0.05 | threshold |
| R3 | Bonferroni p < 0.05/n within program | threshold |
| R4 | fixed effect size, \|u_z\| ≥ 2.0, no correction | threshold |
| R5 | top 2% of genes per program | quantile |
| R6 | top 10% of genes per program | quantile |
| R7 | top 200 genes per program | fixed count |

R5 is the convention used by PerturbHD (Bereket & Leskovec, bioRxiv 2026,
doi:10.64898/2026.04.23.719015), which defines hits as perturbations in the top
2% of MSigDB Hallmark gene-set activity. It is included because it is the hit
rule of the one public evaluation of perturbation-prediction models that operates
on the same gene-set collection this project uses.

Hits are counted on the **signed** statistic in the project's own direction
(positive `u_z` = the knockdown pushed the program down) for the quantile and
fixed-count rules, and on \|u_z\| for the threshold rules, matching `src/sweep.py`.

## 4 · The estimate, fixed before running

For each rule, the **shipped** `denali_audit.core.audit()` — imported from the
package, never reimplemented — is called on that rule's `(sizes, hits)` and its
`r2_size_alone` and `verdict` are recorded verbatim. Using the shipped function
is the point: this arm must measure what a caller would actually be told.

## 5 · The decision rule, fixed before seeing any value

- **If all seven rules return the same verdict:** the verdict is robust to
  hit-calling. No scope limit is added, and I report that the concern was
  unfounded, in the same place I would have reported the defect.
- **If the verdict differs across any two rules:** denali's verdict is in part a
  function of the caller's convention. That becomes a **scope limit the same day**,
  and the shipped tool must say so **on its own output** — not in a footnote in a
  document nobody opens.
- **If the verdict is identical but the R² range across rules exceeds 0.20:** the
  verdict is robust while the estimate is not. Report both facts and add the range
  to the tool's output rather than a verdict change.

## 6 · The reading I must not allow, fixed in advance

R5, R6 and R7 fix the hit count per program by construction, so their hit column
is constant or near-constant and their R² is **expected to be near zero**.

**If that happens it is not evidence that such rankings are unconfounded.** It is
evidence that this diagnostic cannot see the power difference under a rule that
fixes the count. The underlying asymmetry — larger programs yield more precise
statistics — is unchanged by the choice of hit rule; the quantile rule only makes
it invisible to *this* instrument, by moving it out of the hit count and into the
within-program ordering, which the audit never reads.

So a near-zero R² under R5–R7 must be reported as **the diagnostic going blind,
never as the ranking coming back clean.** A tool that answers "NOT
SIZE-DOMINATED" on a top-N hit list while being structurally unable to detect the
problem is issuing a false reassurance, and that is the defect this arm is looking
for. Written here so the framing cannot be chosen after the numbers are visible.

## 7 · Kill criteria and what would make this arm wrong

- **One screen.** This is denali's own K562 screen and nothing else. It cannot
  establish how the rules compare in general, only that they differ or do not on
  a real screen. n = 1 screen, 50 sets.
- **The collapse gap in §2** means absolute values are not the project's headline
  and are labelled so on every surface they reach.
- **Masking, not imputing**, means the per-program gene count varies slightly
  between programs with non-finite entries; the same mask is applied to every rule
  so the comparison is not affected, but the absolute counts carry it.
- **`audit()` may return `UNDETERMINED`** for a degenerate hit column. That is a
  legitimate outcome and is reported as itself, not as a missing value.
- If a rule cannot be computed at all, its row is left **empty**. An empty row is
  honest; an estimated row is not.
