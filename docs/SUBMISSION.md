# Submission copy — paste-ready

> ⚠ **THE EVENT WAS NOT ENTERED.** This file was written for a hackathon
> submission that did not happen. It is kept unedited as a record of the work,
> not as a live plan, and nothing downstream depends on it. The project is a
> standalone piece of work; `README.md` and `REPORT.md` are the current
> statements of what it is and what it found.

Every number below is carried from `results/` and enforced by the invariant
suite. If a figure here disagrees with the repo, the repo is right and this file
is stale — say so rather than reconciling it live.

**Track A — Build an AI Scientist.**
**Team:** Alex · Rachel Selbrede.
**Repo:** https://github.com/alejandro-publius/denali (public, MIT)
**Live:** https://alejandro-publius.github.io/denali/

---

## Name

**denali**

## Tagline (≤ 200 characters)

> An AI scientist that audits genetic screens — including its own. It scored 50
> biological programs against 9,837 CRISPRi knockdowns, ran thirteen evaluations,
> and seven came back negative. All thirteen are reported.

Alternate, if the field is shorter:

> Thirteen evaluations. Nine negative. All thirteen reported. An agent that audits
> genetic screens, and halts itself when its own rules say stop.

## Elevator pitch

A genetic screen hands a lab a ranked list of thousands of hits, and validating
the top of that list costs a year and six figures. denali is the check you run
first. It reads a finished screen back and estimates how much of the ranking is
explained by **how the gene sets were built** rather than by any biology.

On our own screen the answer is most of it: **56–75%** of the variance in which
programs look "reversible" is explained by a model that never looks at what a
program does. Program size alone explains **46.5%**.

Then we ran the identical command on **seven other groups' published screens**,
where **36–88%** of each ranking is explained by set construction alone — and on
a corpus of **1,272 published screens**, where the field's median is **0.224**.
The confound is not ours. It is arithmetic, and it is everywhere.

---

## Inspiration

We started out trying to build a discovery tool: name a biological program, and
rank every knockout in a genome-scale screen by how hard it pushes that program
the other way. We built it. Then we asked the question underneath it — *how much
of this ranking would exist if the biology were random?* — and the honest answer
turned the project inside out.

Our primary program failed first. We picked the unfolded protein response,
pre-registered a gate, passed it 3/3, and the arm came back empty: none of the
canonical UPR regulators were recovered. The reason is nameable — K562 is an
unstressed leukemia line, so the program was never engaged. A held-out program
we had not scored succeeded on the same code the same night. That contrast is
what made the measurement question unavoidable.

## What it does

**It scores.** 50 MSigDB Hallmark programs against 9,837 CRISPRi knockdowns from
a published genome-scale Perturb-seq screen (K562), classical statistics
end-to-end, no neural model anywhere in the scoring path.

**It audits itself.** A model of six *measurability* features — none of which
know what a program does — recovers 56–75% of the variance in apparent
reversibility. It is a range and not a point because one of the six is computed
from the same matrix as the outcome; **0.561** is the figure that survives that
objection and we never quote the top alone.

**It chooses its next step and halts.** The agent picks which program to read by
a stated policy, updates a running estimate, emits a next experiment, and stops
when the estimate stops moving. On halting it reports that stopping early
**overstated its own answer by 0.081**, and names the gap. No branch in that code
tests a program's name — `grep HALLMARK_ src/next_experiment.py` returns nothing,
which is the claim stated as a property of the code rather than an assertion
about intent.

**It audits other people's screens.** `src/audit_screen.py` takes the table any
gene-set analysis already produces — set, size, hits — and reports the same
estimate for your screen. We ran it on seven published external studies and on
1,272 screens from the literature.

**And then it asks whether the field knows.** Of the 187 publications behind
those 1,272 screens, 111 are open access, and **4 of them — 3.6% — mention
gene-set size anywhere in the full text.** Pre-registered before the run, with a
positive control that fires on three enrichment-methods papers, because a 3.6%
rate and a broken search look identical without one. It measures **mention, not
understanding**, over a 59.4% denominator, and both limits are stated wherever
the number appears.

**It ships as a tool, not only as a result.** An MCP server exposes the frozen
matrix to any agent; a static results page runs with **zero network calls**; a
Streamlit view reads the same frozen tables. Nothing recomputes at view time.

## How we built it

The spine is deliberately boring: pseudobulk differential expression,
Mann–Whitney signed-z, Benjamini–Hochberg FDR, OLS. What is not boring is the
scaffolding around it.

- **Pre-registration, hashed before the value existed.** Thresholds were written
  down and committed before any number they judge was computed. The held-out
  program list was sealed at **08:24:14**; the scoring code was first committed at
  **08:52:32**. The held-out target was fixed before the code that scores it
  existed, and the 28-minute gap is checkable in the commit graph.
- **A byte-frozen scorer.** Every sweep verifies the scorer's sha256 on load and
  aborts if it moved. If that hash changes, the run is not the one these numbers
  came from.
- **555 automated checks** that hold the prose to the data. The findings table in
  the README is the single source of truth; 15 restatements of the count across 7
  files fail the build if any one drifts.
- **A clean-clone reproduction check.** Clone at a commit, run `make all`,
  and `git diff` must be empty. It is.

## Challenges we ran into

**A judge's question broke our headline, and we kept the question.** Someone
pointed out that three of our six "measurability" features are properties of the
gene *set*, not of our measurement. They were right. Stripped apart, measurement
features alone give adjusted R² of **0.15**; set-construction features alone give
**0.70**. Set size by itself beats all three measurement features combined, three
times over. The number stood; the word "measurement" did not. That check is
post-freeze, it is labelled post-freeze, and the repo records that a critique
prompted it rather than our plan.

**Our own quality filter was wrong 20 times out of 50.** We built the
measurability gate anyone building this would build, then checked it against all
50 programs instead of only the ones it approved. Twenty fail the gate and
produce hits anyway; exactly one passes and produces nothing. The held-out
program fails our own filter — expression ratio 0.92 — and ranks 11th of 50 with
773 hits. We would have thrown away our best result. The gate was withdrawn as a
trust signal, and its failure is reported as a primary finding.

**Three of our checks were silently not running.** One was gated on data a clean
clone does not have. One was keyed to a commit a rebase had erased. One matched
markup that had since been rewritten. All three passed while testing nothing —
because a skipped check and a passing check look identical in the output. The
self-counting badge caught two of them, since a skipped check still changes the
count. All three are now content-addressed rather than reference-addressed.

**Guide-pair concordance came back at −0.019**, which kills gene-level claims
outright. Rather than ignore it, we drew the line where the data puts it: **this
project names no novel gene anywhere** — not in a table, a figure, a label, a
slide, or a spoken line. Every claim is pathway-level.

**We disclosed a partial-visibility incident nobody asked about.** During the
held-out run the script crashed twice, and three of ten rows had printed before
the guard was written. It is in the limitations because we wrote it down, not
because someone found it. The result was a *failure* — contamination biases
toward looking good, and this came back worse than chance with zero true
positives.

## Accomplishments we're proud of

**Nine of thirteen evaluations came back negative, and all thirteen are reported.** One
returned no verdict at all because our own pre-registered power rule fired
against us, and we did not refit.

**A rule we wrote in advance stopped the machine twice.** The held-out evaluation
halted at 1-of-10 programs passing against a floor of 8-of-10. The annotation arm
halted on a power rule that fired on 3 of 4 collections — and in the same arm our
predicted *direction* was wrong, which we also report. The halts are the point: a
loop that only ever continues is not being governed by anything.

**The last lap turned the audit on itself and cost us our own headline.** Having
asked 1,272 published screens how much of their rankings is construction, we
asked the same of our corpus — and the corpus was confounded the same way. Those
screens come from 187 publications; one contributes 26.7% of them. Collapse each
publication to its median screen and denali moves from roughly the 90th
percentile to the **73rd**. It leads that writeup *because* it costs us the
number.

**The positive result is labelled a control, because that is what it is.** Run
unchanged on a pathway it was never tuned for, the ranking puts that pathway's
known master regulator at **rank 2 of 11,258**, with 11 of 17 canonical members
in the extreme 10% (p = 7.0×10⁻⁸) and the correct sign at both tails. That tells
you the ranking works. It does not tell you the ranking discovered anything, and
we do not say that it did.

## What we learned

That the most valuable thing an AI scientist can do is not generate a hypothesis
— it is estimate how much of an existing result is an artifact of how the
question was posed. There is prior art on the mechanism (CAMERA, 2012) and on the
framing (2021). Our contribution is not "we found something new." It is **we
measured what it costs you on a real genome-scale screen, and built the check as
a tool anyone can run in one command.**

And that the dangerous failure in a verification suite is not the assertion that
is wrong. It is the assertion that quietly stops executing.

## What's next

The Virtual Cell Challenge round two opens **20 August 2026**, four days after
this event, with announced scope covering combinatorial perturbations and
cross-cell-type generalization. Their own 2025 post-mortem notes that purely
AI-based approaches did not consistently beat statistical baselines — which is
the same finding this project arrived at from the other direction. The audit
generalizes to any screen that produces a set/size/hits table, and the corpus arm
is the start of a field-wide baseline rather than a one-screen curiosity.

Nearer term: the three remaining pre-registered evaluations are authored but not
containerized, and the off-target arm's method audit wants a second cellular
assay before any of it is worth more than a construction statistic.

## Built with

`python` · `numpy` · `pandas` · `scipy` · `statsmodels` · `h5py` · `streamlit` ·
`mermaid` · Claude Code · Paperclip · Modal · Model Context Protocol ·
CZ Biohub ESMC · Proto (Evo Design) · Benchflow · GitHub Pages

Two of these do more than get imported. **Paperclip is both an audited object
and an instrument**: we probed its retrieval with 20 genes and 19 came back with
the same unrelated paper (FIG 4), and then used it properly for evaluation 11's
literature audit over 187 publications — the failure and the working use are
both reported. **BenchFlow carries three tasks** — two on the findings, one on the product — in
`benchmarks/`: `denali-gate-trap` (predict which programs returned hits, given
only measurability — the naive filter scores 0.6981) and
`denali-confound-estimate` (estimate the size confound on seven real published
screens, truth spanning 0.36–0.88), plus `denali-size-carried`, which scores
whether an agent can apply the correction the tool ships rather than restate what
we measured — which entries of a published top ten are carried by set size,
graded against the size-aware residual. All three grade other people's agents
deterministically in code, with no model judging; no denali result depends on any
of them.

Honest tool status — including what we set up and deliberately did **not** use,
with the reason — is in [`docs/TOOLS.md`](TOOLS.md), and an automated check fails
the build if an "unused" claim stops being true.

## Try it out

| | |
|---|---|
| Results page (zero network calls) | https://alejandro-publius.github.io/denali/ |
| Repository | https://github.com/alejandro-publius/denali |
| Audit your own screen | `pip install -e packages/denali-audit` then `denali audit <your_table.csv>` |
| Watch the agent choose and halt | `python -m src.next_experiment --demo` |
| Falsify the loop claim in ten seconds | `grep -n 'HALLMARK_\|REACTOME_' src/next_experiment.py` |

---

## Pre-submission checklist

- [ ] Devpost fields pasted from above
- [ ] Video uploaded and link tested in a logged-out browser
- [ ] Repo link tested logged-out
- [ ] Hosted page loads with wifi off (clone + double-click `index.html`)
- [ ] Team members added on Devpost
- [ ] Track A selected
- [ ] Sponsor tools tagged to match `docs/TOOLS.md` — do not tag a tool we declined
