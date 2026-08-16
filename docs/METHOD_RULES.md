# Method rules

The rules this code actually obeys. Rewritten for this repository — each one is
here because it changed a decision in it, not because it is good advice in
general.

---

## Inference

**The unit of inference is stated before the test, and it is never the
convenient one.** In this project the unit is the *program*, not the gene. That
is not a stylistic choice: guide-pair concordance is **−0.019**, so two
independent reagents against the same gene disagree, and any per-gene number is
noise. Program-level statistics aggregate over ~11,000 perturbations and survive
that. The per-gene divergence table was deleted from the frozen interface for
exactly this reason.

**Report effect sizes and full tables, not significant rows.** Every score for
all 9,837 knockdowns against all 50 programs is in `results/frozen/matrix.csv`.
Nothing was filtered before saving.

**Know what your test can and cannot return.** A statistic has a floor and a
ceiling set by its design, and if you do not compute them first you will
interpret an artifact. Here: a set-level statistic gives larger gene sets more
power, which is why set size explains 46.5% of the outcome — and why the
post-freeze check that isolated it was the single most important thing we ran.

**Check confounding before interpreting.** Ours was essentiality: knocking out a
gene the cell needs moves everything. So DepMap fitness data is joined to every
row and results are tiered by it, rather than assuming the top of a list is
biology.

## Pre-registration

**Write the threshold before the value exists, and hash it.** Two
pre-registrations in this repo, both committed before the analyses they judge.
The matrix pre-registration named the primary claim, the alternative claim, the
statistic that decides between them, and what would make us report neither.

**Name the alternative claim, not just the hypothesis.** We wrote down in
advance that if measurability explained the variance, *that* becomes the finding
rather than the failure. It did. Because it was pre-registered, it is a result.

**A criterion is never revised after seeing the data.** When the held-out test
failed we reported the failure. When a bug forced a mid-run patch, the patch was
disclosed rather than the run restarted quietly.

**Seal what you want to be believed.** Choosing the held-out program and
committing it before the scoring code existed is the strongest evidence in this
project, and it cost nothing but ordering.

## Evidence

**External data decides; the model may propose but never self-certify.** Every
quantitative claim here comes from deterministic code checked against something
outside it: DepMap, MSigDB, or a commit timestamp.

**Distinguish association from mechanism, and label them differently.** This
project produces transcriptional movement. It does not produce phenotypic
reversal and does not claim to.

**Audit your retrieval instead of trusting it.** Literature tools return
plausible sources that do not support the specific claim. Measured here: 34
distinct sources for 113 genes, one review covering 50.4%, and 19 of 20
blind-probe genes returning the same unrelated methods paper. We call the result
a pointer layer, not an evidence chain.

**Expect silent wrong answers from public infrastructure.** Measured in this
project: a perturbation matrix that is effect sizes rather than expression,
non-finite entries that must be masked rather than imputed, two regexes that
parse the same identifiers into different gene counts, and an essentiality
statistic averaged over 1,178 cell lines that disagrees with the one line we
actually used. Each was found by checking, not by assuming.

**Preserve negatives.** Three of four evaluations here are negative and all four
are reported. A null from working machinery is a finding; the positive control
is what makes it one.

**Enforce the scope rule where the caller is, not only where you are.** Our
build-time guard stops us publishing a gene-level claim. It does nothing when an
agent queries the server, and the agent is the caller we cannot see. So the
callable surface refuses a bare gene symbol and refuses to rank or nominate,
before it reads any data. Prior art, and worth citing rather than reinventing:
CRISPR-GPT (Wu et al., *Nature Biomedical Engineering* 9:245, 2025) hard-codes
non-bypassable refusals and a single "I don't know" path rather than trusting the
model to be careful. Different risk surface, same instinct.

## Practice

**Freeze the interface before building anything on top of it.** Everything
downstream — the page, the callable tool, the figures — reads
`results/frozen/` and recomputes nothing.

**Disclose your own mistakes in the artifact.** `LIMITATIONS.md` §7 lists the
process failures we found in our own work: two mid-run crashes, a denominator
error, two wrong tier labels, and a statistics bug in our own freeze code.

**Do not add a tool to inflate a count.** Where an integration was blocked or
unavailable, it is listed as not done rather than faked with a package that
happens to share the name.

**No claims about how fast this was built.** The work stands on what it measured.

---

## Historical migrations, not part of the reproduction path

`src/divergence_repair.py` is a one-shot migration that ran once and **deletes
its own input**. It converted a per-gene verdict table into program-level counts
after guide-pair concordance made per-gene calls indefensible. It cannot run a
second time and is excluded from `make all`.

That exclusion was not foresight: `make all` originally included it, and the
first clean-clone reproduction check died there at step 5 of 9. Recorded because
a reproduction path that has never been run from a clean clone is a claim, not a
fact.
