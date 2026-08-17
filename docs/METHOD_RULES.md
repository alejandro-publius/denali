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

**Preserve negatives.** Ten of fourteen evaluations here are negative and all fourteen
are reported. A null from working machinery is a finding; the positive control
is what makes it one.

**A check is not evidence until it has been observed to fail for the reason it
exists.** Assert the failure mode, not only the success. A new green check should
be assumed broken until it has been made to go red on purpose.

This is here because it happened three times in one day, to two sessions working
on the same repository, and not one of the three was caught by reading the code:

- A guard written as `"0.214" in text and "concordance" not in text` could never
  fire, because nearly every file here names `results/concordance/` and the
  second clause was always false.
- A guard named "README states the derived confound too" opened
  `benchmarks/challenge/README.md`. It fired correctly for that file — the
  defect was the **name**, which advertised coverage of the top-level README,
  the one surface where the wrong number had actually shipped. A misnamed check
  is worse than a dead one: a dead check leaves you unprotected, a misnamed
  check leaves you unprotected while reporting that you are not.
- A guard asserting that three values each appear "somewhere in the README"
  passed when one of them was corrupted, because all three also occur elsewhere
  in the file. It tested the presence of strings, not the claim they were
  written to protect.

All three were found by mutation and none by review.

**Mutate the guard's inputs as well as its subject.** A fourth case appeared the
same day, in the block written to codify the three above, and it is the one
"mutate it until it goes red" does not catch. Three new checks sat inside
`if paired_programs.csv.exists() and readme:` with no `else`. Remove the file
and they do not fail — they **vanish**, and the suite prints a smaller green
number indistinguishable from the larger one. Four content mutations had been
run against those checks and not one touched it, because every one left the file
present and exercised the true branch.

So the four ways a guard can be green and empty are all different, and only the
first three share a fix:

| the guard | why it could not fail |
|---|---|
| `"0.214" in text and "concordance" not in text` | a clause that was never false |
| `README.md` pin naming a file it did not open | a path that was never read |
| three values "somewhere in the README" | a string that occurred elsewhere |
| three checks behind `if <file>.exists()` | a branch that was never entered |

Preconditions are therefore asserted rather than gated: `test_cross_surface.py`
now fails if any input its conditional blocks read is absent, so a deleted file
is loud. Twenty of that file's checks sit inside such a conditional, which is
fine per block and dangerous in aggregate — the aggregate is what is now
guarded, and it was verified by deleting an input and watching the total drop
from 46 to 43 with one loud failure naming the cause.

**Four more shapes, found the same day by three sessions checking each other.**
They are listed separately because they share a symptom and not a fix, and
because "mutate it until it goes red" catches none of the last three.

| the guard | why it could not fail | what catches it |
|---|---|---|
| verified on one member of a class | `log10(1+0)` is exactly 0.0, so an `ss_tot == 0` test fires on the all-zero fixture it was built from. For most other constant hit columns the same expression lands near 9.7e-30, the test does not fire, and the tool divided by a denormal and reported the garbage beside a confident verdict. Eight of seventeen constant values leaked | mutate across **several** members of the class, never one |
| half of a biconditional | the findings table was checked prose-against-table in one direction. Nothing checked artifact-against-table, so an arm could ship with a results directory, a pre-registration and a module and never get a row | write the converse and mutate it too |
| a fixture drawn from the null | `hits = size * 0.08 + noise` **is** the binomial null's data-generating process. The positive control for this project's central claim was a no-biology sample asserted to be CONFOUNDED. It passed because the band had no null behind it | ask what a fixture's no-biology value is before asserting a verdict on it |
| unreachable where it matters | `test_mcp_stdio.py` appeared in neither the Makefile nor CI, and could not have run there if added: its interpreter was hardcoded to a `.venv` neither environment creates, so it would have printed SKIP and exited 0 forever. It was the only automated evidence the server starts, guarding a bug that had already shipped once | check that the suites CI claims to run actually ran |

The last one has two independent halves and fixing either alone leaves it
broken — it was absent from the environments that gate a push, **and**
structurally unable to run in them.

**An isolation test must not depend on import resolution order at all.** Two
guards written to prove `audit.html` ships a working package both passed while
it shipped a broken one. The second wrote the page's inlined modules to a temp
directory and imported `denali_audit` there — first with `cwd=`, then with
`sys.path.insert(0, tmp)` — and both times imported the real installed package
instead, silently, in the direction that says everything is fine.

The fix is to import under a package name no distribution owns, so nothing can
shadow it. **The reason is stated carefully because the first reason given was
wrong.** It was recorded as "an editable install registers a meta-path finder and
`meta_path` precedes `sys.path`". Another session measured it rather than
believing it: here `_EditableFinder` sits *last* on `sys.path`, after
`PathFinder`, and a decoy package at the front of `sys.path` wins. That mechanism
does not hold in this environment and the entry would have taught the next person
something false.

Three independent things can defeat such a test — `sys.modules` caching, a
meta-path finder that inserts itself early, and path ordering — and all three
fail toward "everything is fine". So the rule is not about any one of them: **do
not build isolation on resolution order, because you cannot see which of the
three you got.** Import under a name nothing else can claim, and the question
stops arising.

A fifth, from the same day and the same file this rule is written in: the list of
count-stating surfaces was **enumerated**, so a fifth surface could state the
count and nothing read it. One had — a demo script told a presenter to expect a
figure wrong by 78. Enumerating what to check is the same weakness as
enumerating what to inline: discover the set instead. Both are now discovered.

The cost of the discipline is one minute per guard; the cost of skipping it is a
guard that reports safety it does not provide, which is strictly worse than no
guard, because it stops anyone looking again. The same argument the rest of this
file makes about skipped tests applies to passing ones nobody has falsified.

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
