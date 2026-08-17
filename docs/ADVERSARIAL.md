# The hostile read

Written by us, against us, on the night before submission. The premise: a judge
who wants to find the weakest link, has read the repo, and is not impressed by
volume.

**For each criterion: the single question that most exposes us, and our actual
answer.** Where the answer was weak and the fix was cheap, it was fixed and this
file says so. Where it was weak and the fix was not cheap, it stays here
unfixed, named plainly. Being first to say it is worth more than hoping nobody
asks.

---

## Criterion 1 — closing the loop

### The question that most exposes us

> **"Your loop closes against a CSV, not a cell. Nothing you propose was ever
> run. How is that a scientist?"**

**Conceded, and it is the real limit of the whole project.** Not one proposed
experiment in this repository has been performed. The loop reads a finished
screen, proposes a next condition, and stops. Whether raising depth would in
fact recover the null programs is unknown and unknowable from here.

What we will defend is narrower and, we think, still worth something: **the
proposal is a function of the measurement, not of the program's identity.** Hold
the program fixed and change only its measured outcome, and the proposal changes
with it:

| `HALLMARK_MYC_TARGETS_V1`, hits forced to | outcome | proposal |
|---|---|---|
| 5,707 (as measured) | `HIT_ABOVE_THRESHOLD` | validate at pathway level, both tails, second cell type |
| 900 | `HIT_ABOVE_THRESHOLD` | same |
| 40 | `WEAK` | underpowered — raise depth or merge with a related program |
| 0 | `NULL_WITH_MECHANISM` | power limit, not biology — change the condition and re-run |

The falsification condition moves too, not just the prose. And
`grep -n 'HALLMARK_\|REACTOME_' src/next_experiment.py` returns nothing, so the
claim is checkable in one command rather than taken on trust.

### The follow-up that lands harder

> **"That is a deterministic branch on a threshold. It is a lookup table with
> good manners, not an agent."**

**Largely true of `next_experiment.py`, and we would rather have it that way.**
An auditable branch on a measured value is worth more here than an LLM call
nobody can reproduce, in a project whose entire claim is that most apparent
discovery is artifact. A generated proposal would be one more unfalsifiable
output.

The agent-shaped part is not the proposal text. It is the **selection and
stopping**: the loop chooses which program to read next by a stated policy,
maintains a running estimate, halts when the estimate stops moving, and then
reports that stopping early **overstated its own answer by 0.081**. Over eight
laps, three stopped on rules fixed before the run — two halting outright, one
gating its own question behind an engagement test that could have returned
nothing. **A loop that only ever continues is not being governed by anything.**

That is still a modest claim. We are not claiming autonomy.

---

## Criterion 2 — inspectability

### The question that most exposes us

> **"You have 370 assertions. How many of them were actually running?"**

**This is our best answer and it was earned the hard way.** Four separate guards
in this repository passed while testing nothing: one gated on data a clean clone
does not have, one keyed to a commit a rebase erased, one matched markup that had
been rewritten, and one — the counter itself — carried a hand-maintained offset
so that checks added below it were silently uncounted.

All four were found, all four are fixed to be content-addressed rather than
reference-addressed, and the mechanism that caught two of them is the suite
counting itself: **a skipped check and a passing check look identical in the
output, but they change the total.** The README states that total in three
places and `docs/SUBMISSION.md` in a fourth; all four fail the build on
disagreement. CI, which uses a shallow checkout and installs none of the sponsor
tooling, reports the same number as this machine.

The honest residue: we know about four because we looked. We do not know there
were only four.

---

## Criterion 3 — validation

### The question that most exposes us

> **"You found no biology. Everything you report is a null. Isn't 'we measured
> nothing' the expected outcome of measuring nothing?"**

**By construction, and it needs saying earlier than we say it.** This project
does not attempt to discover a gene. Guide-pair concordance is −0.019, which
forbids gene-level claims outright, so the ceiling on what we could ever have
found was set before we found anything. A reader who arrives expecting a
discovery will read seven negatives as seven failures.

**Fixed tonight:** the README's opening now leads with what the tool is *for* —
the check you run before committing a year to a hit list — rather than with the
coefficient. The framing was always in the repo; it was below the fold.

### The second question, which is sharper

> **"Your corpus number is a different estimand from your headline. You are
> comparing 0.465 to 0.224 as if they measure the same thing."**

**Correct, and it is disclosed — but the caveat should be impossible to miss and
currently it is merely present.** The corpus arm computes size-alone R² over
published hit lists whose significance thresholds, libraries and phenotypes we
do not control; our 0.465 comes from one screen scored by one frozen scorer.
They are not the same quantity, and `docs/CORPUS.md` says so.

The arm also turned on itself and found its own corpus confounded the same way
the field is: 1,272 screens from 187 publications, one contributing 26.7% of
them. Collapsing to publications moves us from roughly the 90th percentile to
the **73rd** — a correction that costs us the number, and it leads that writeup
for exactly that reason.

### The strongest thing we have, added tonight

`src/independent_recompute.py` reimplements the headline statistic from the
README's method section, without reading `src/score_k562.py`, `src/sweep.py` or
`src/freeze_predictor.py`, using scipy's Mann–Whitney, statsmodels' BH
correction and statsmodels' OLS in place of the frozen path's own. It reads the
raw substrate, not `results/frozen/`. Its agreement with the published figures
is asserted by an invariant to a stated tolerance.

**What it does not establish:** that the method is right. Two implementations of
a wrong method agree with each other. It rules out implementation error in the
frozen scorer; it does not rule out the question being the wrong one to ask.

---

## Criterion 4 — sponsor tools

### The question that most exposes us

> **"You used a literature tool and then said its results were unusable. Which
> is it?"**

**Both, and reporting both is the point.** We probed Paperclip's retrieval with
20 genes and 19 came back with the same unrelated paper — a zebrafish methods
paper — so the evidence layer is a **pointer layer** and is labelled one
everywhere. Nothing it returned feeds a reported number.

Then we used the same tool properly, for a question it is actually good at: of
the 187 publications behind the corpus arm's screens, how many discuss gene-set
size at all. Four of the 111 that are open access. That arm is pre-registered,
carries a positive control that must fire on three enrichment-methods papers,
and is labelled as measuring **mention, not understanding**.

A tool that fails at one task and works at another is the normal case. Reporting
only the half that flatters the submission is the thing we are trying not to do.

---

## The thin ones, named

Three places where our own numbers are weaker than a skim suggests. All three
are already disclosed somewhere; the question is whether they are prominent
enough, and for two of them the answer was no.

| Claim | Why it is thin | Where it is said |
|---|---|---|
| **Evaluation 5 clears its bar by 0.026** | Pre-registered at ≥0.25 and it returned 0.2758. That is a pass, and it is a thin one. If the threshold had been 0.28 it would have failed. | README findings row, `docs/RPE1_PREREG.md`, and the handoff calls it thin |
| **RPE1 is not a replication** | It covers 24.3% of K562's targets and that quarter is disproportionately the essential-gene subset — 94.1% of essentials against 11.3% of non-essentials. Calling it independent replication would be the easiest available overstatement. | Published as a **FAIL** control |
| **Evaluation 11 is labelled POSITIVE** | It is a positive in the narrow sense that a pre-registered branch fired as predicted, not in the sense that we found something good. Three of thirteen now read POSITIVE, and a skim could take that as three wins. | This file, and the findings row states the branch |

---

## What we would still lose points on

Stated because a judge will find them anyway.

1. **No experiment was run.** The loop is closed against data, not against a cell.
2. **The predictor failed its held-out test** — balanced accuracy 0.4375, worse
   than chance, zero true positives — and was not refit. We report it as a
   failure. What survives is descriptive, over the 50 programs we did score.
3. **One cell line, unstimulated.** K562 is a leukemia line with no ER stress,
   which is why our own first program failed its known-regulator control.
4. **The literature audit measures mention, not understanding**, over a 59.4%
   open-access denominator.
5. **Two implementations agreeing does not make a method correct.**
