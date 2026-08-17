# Demo — under 3 minutes spoken, and the tool runs live

> ⚠ **THE EVENT WAS NOT ENTERED.** This script was written for a hackathon
> submission that did not happen. It is kept because it is the shortest honest
> account of what the tool does, and it has since been rewritten around running
> the tool rather than narrating the study. `README.md` and `REPORT.md` remain
> the current statements of what this is and what it found.

**Read the bold. The rest is stage direction.** `[pause]` = stop, let the screen carry it.
**The repeated number is TEN OF FOURTEEN.** It lands in the close.
**Two beats are LIVE.** They are real commands against a real table, not a recording,
and both are in `make judge-check` so they run with no network and no key.

**Rehearse this once.** Run `make judge-check` before you speak: it executes both
live beats end to end and prints exactly what the audience will see.

---

## OPEN — the problem, one breath

> ### **"A genetic screen hands you a ranked list of thousands of hits. Chasing one costs a year and six figures, and more than half of preclinical research does not reproduce. This is the check you run before you pick which one."**

`[pause — 2 beats]`

---

## 1 · The finding — and why it is arithmetic

> **"We measured how much of that ranking is explained by how the gene sets were built rather than by any biology. On a published genome-scale screen, set size alone explains forty-six and a half percent of it."**
>
> **"It is the crime-count problem. A pathway with two hundred genes returns more hits than one with thirty regardless of what either does — the same way a raw crime count always ranks the biggest cities as the most dangerous. Nobody divides through by size."**

*Screen: **FIG 3**. The size-alone figure on it is **46.5%**.*
`[pause]`

---

## 2 · LIVE — install it, and audit a real table

*Type both lines. They take about four seconds.*

```bash
pip install -e packages/denali-audit
denali audit examples/example_gprofiler.csv
```

> **"That is the tool, not a figure. One line to install, and it reads the table your analysis already produced — no renaming a column, because a check that asks you to reshape your data first never gets run."**

*Screen: the verdict block. Let it sit before reading the second half.*

> **"Verdict: confounded. Forty-six percent of this ranking is predicted by how the sets were built, with no reference to what any gene does."**
>
> **"Then the part I care about. An R-squared is not a judgement until you know what normal looks like, so it puts you against one thousand two hundred and seventy-two published screens. This one is worse than nine in ten of them."**
>
> **"That table is our own screen. The tool says it about us."**

*The percentile line reads: 90% of 1272 published screens are less explained by set size than yours. The field median is 0.224 against this screen's 0.465.*
`[pause]`

---

## 3 · LIVE — apply the correction, and watch our own headline fall

```bash
denali rerank examples/example_gprofiler.csv --top 10
```

> **"Now it applies the correction it just named, and shows what moves. Of our own top ten, three hold their place once set size is accounted for and seven do not. Our number one — the largest set in the collection — falls to twenty-fourth."**

*Screen: the seven rows that leave the top ten. Point at the first one:*
`HALLMARK_MYC_TARGETS_V1`, 194 members, 5,707 hits, **rank 1 → 24**.

> **"Note what it refuses to do. It does not tell you the three survivors are real, and it does not hand you a shorter list to chase. Its own output says so. It tells you which entries your ranking cannot justify — a tool for deciding what not to chase, and that is where the money goes."**

`[pause — strongest beat in the talk]`

---

## CLOSE

> **"We ran fourteen evaluations on this project. Ten of them came back negative. All fourteen are reported, and the ones that were not pre-registered say so. Scope is pathway-level only, because guide-pair concordance is −0.019, so we name no novel gene anywhere. And a test requires the installed package to reproduce the published figure exactly, so the tool and the paper cannot drift apart. Take it apart."**

---

# RUNNING THE LIVE BEATS

Both commands are step 3 and step 4 of `make judge-check`, so the safe rehearsal
is to run that target and read its output. It needs no download, no API key and
no network.

| If | Do this |
|---|---|
| `pip install` is slow or the venue has no network | Skip it and prefix instead: `PYTHONPATH=packages/denali-audit python -m denali_audit.cli audit …`. Same code, no install step. |
| Someone asks for their own file | `denali formats` lists what is read without any flags. Anything else: `denali audit FILE --set <col> --size <col> --hits <col>`. |
| The whole live section has to go | `make judge-check` prints both beats in one command; run it and narrate the output. |

---

# PREPARED RESPONSES

## ⚠ "You showed me your own screen. Isn't that the one you tuned it on?"

> **"It is our own screen, and that is the point — the tool demotes its author's top hit by twenty-three places. We also ran the identical command on seven other groups' published supplementary tables, where thirty-six to eighty-eight percent of each ranking is explained by set construction alone. One of those comes back only partially confounded, and one table was refused outright for having no true hit count, so it discriminates rather than flagging everything."**

## ⚠ Partial visibility of the held-out set — lead with point 1

*If asked: "Three rows printed before you patched the crash. You saw part of the held-out set."*

> **1. "The result was a FAILURE. Contamination biases toward looking good. It came back worse than chance with zero true positives — you can't peek your way to that."**
>
> **2. "The frozen predictor, hash 610f2a75, was never touched. Only feature extraction changed, and the hash is verified at load time."**
>
> **3. "The guards are neutral by construction — undefined features fall back to the training mean, so they contribute zero."**
>
> **4. "And the inconclusive verdict fired on a pre-registered rule — one of ten, below the eight-of-ten threshold — before any number was visible."**
>
> **"It's in LIMITATIONS section seven because we wrote it down, not because you found it."**


## ⚠ The question that broke our headline — say it straight

*If asked: "Three of your six 'measurability' features are properties of the gene set, not of your measurement. Strip them and what's left?"*

> **"You're right, and we ran it after someone made exactly that point. It collapses. Measurement features alone give adjusted R-squared of fifteen percent. Set-construction features alone give seventy percent. Set size by itself beats all three measurement features combined, three times over."**
>
> **"So an earlier version of our headline attributed the variance to measurement, and it's carried by how the gene set was built. We corrected it — the number stands, the word 'measurement' didn't. That check is post-freeze, it's not pre-registered, and it's in the repo under results slash sensitivity with a note saying a critique prompted it, not our plan."**

**Do not soften this.** The honest version is stronger than a hedge, and the
alternative is being walked into it.


## ⚠ "How do you know any of this is right?" — the validation answer

*Lead with 1. It is the strongest and it needs no timestamp.*

> **1. "We ran a held-out evaluation and it failed. Ten programs we had never scored — underpowered, inconclusive, balanced accuracy 0.4375, worse than chance, zero true positives. We report it. A system that only ever reports its successes has no external standard by definition."**
>
> **2. "Seven controls, four of them failing, all reported. Random genes return nothing. Canonical regulators land where they should on one program and nowhere near it on another — that second one is our null."**
>
> **3. "DepMap is an independent screen we did not run. Every row is joined to it and tiered by it, so 'this knockout moves the program' is separated from 'this knockout kills the cell.'"**
>
> **4. "Thresholds were written down before the numbers existed — including the rule that declared the held-out inconclusive. That rule fired against us."**
>
> **5. "And the shipped package is held to the paper by a test: it runs the same maths on the frozen research data and has to return 0.4649. If the tool and the paper ever disagree, CI fails instead of the two quietly diverging."**

## ⚠ "Seven negatives — you only showed me the headline." The other arms.

*If asked what the negatives are, or whether the finding generalises:*

> **"Three are on our own screen: most of what looks like biology is set construction; the obvious quality filter is wrong twenty times in fifty; and the held-out test failed. Four take it off our screen. Cross-screen agreement — a quarter of what looks like replication, twenty-six percent, is set size, not biology. Clinical off-target nomination — a methods audit of published nominations, no dosing and no recommendation — where a median of thirty-one percent of the biochemical-versus-cellular agreement is search yield, not the guide. Adamson, where the program is actively engaged rather than dormant: the confound persists, and that arm is pre-registered. And 1,272 published screens: the field's median size-confound is 0.224, ours is 0.465 — above the ninetieth percentile."**
>
> **"And the eleventh asks whether the field says so. Of the hundred and eighty-seven publications behind those screens, 111 are open access, and four of them — 3.6% — mention gene-set size anywhere in the paper. That one is pre-registered, and it measures whether they mention it, not whether they understood it."**
>
> **"That last one is the honest core. Our headline number is atypical in magnitude, and we published that fact rather than bury it. The mechanism is universal; our screen just shows it more clearly."**

*The loop, if asked whether anything chooses for itself:*

> **"It picks which program to read next by a stated policy, updates a running estimate, and stops when the estimate stops moving. It ran eight laps and three stopped on a rule written before the run — two halting outright, one refusing to ask its question until it had proved the program was switched on. When it halts it reports that stopping early overstated its own answer by nought-point-oh-eight-one. No branch in it tests a program name; grep the file for a pathway name and it returns nothing."**

*The positive control, if asked what works:*

> **"We took a program we had not scored and ranked all nine thousand eight hundred knockouts against it. Its master regulator comes back second — that is the textbook answer and we call it a recovered known answer, not a discovery. What a lucky hit does not produce is the shape: seventeen canonical members in the screen, eleven in the extreme ten percent, p equals seven times ten to the minus eight, correct sign at both tails."**

*The second positive, if asked:*

> **"The size effect also reproduces in an independent second cell line, RPE1 — pre-registered at zero-point-two-five, and it clears by zero-point-zero-two-six. A positive that makes the negative stronger, not weaker: the confound is real and it replicates."**

*"So seventy-four percent of the replication is biology?"*

> **"Seventy-four percent is everything we did not remove, not everything that is biology. We took out one thing — set size — and a quarter of the apparent replication vanished. That is a floor on the problem, not a ceiling."**

## Six adversarial questions, ranked by how badly they land

| # | Question | Verdict and answer |
|---|---|---|
| **1** | **"The held-out failed. Why should I believe the predictor?"** | **Fatal to the predictor, survivable for the work.** *"Don't believe it. It failed, we report it as failure, we didn't refit. What survives is descriptive: across the fifty we did score, set construction explains most of the variance. The predictor was the test of whether that generalises, and at n=10 it didn't."* |
| **2** | **"You saw part of the held-out set before patching."** | **Survivable — pre-empt it.** See above; lead with "the result was a failure." |
| **3** | **"Is 0.751 inflated by circular features?"** | **Already answered.** *"Yes, partly, and it's in our first sentence. That's why it's a range. 0.561 excludes the circular feature. We never quote the top alone."* |
| **4** | **"−0.019 — doesn't that kill the pathway claims too?"** | **Survivable.** *"Ranking noise moves individual positions; it doesn't move seventeen genes to both tails at p = 7e-8. Gene-level is dead, pathway-level survives, and that's exactly where we drew the line."* |
| **5** | **"Your rerank is just residuals. That's not CAMERA."** | **True, and stated in the output.** *"The correction is log10(1+hits) regressed on set size, ranked by residual — the tool prints that line so you can disagree with it. It is the cheapest correction that works on a table you already have, which is the only kind anyone runs."* |
| **6** | **"One review covers 50.4% — is the evidence layer real?"** | **Fatal to calling it an evidence chain; we don't.** *"It's a pointer layer and we labelled it one. Our top source for ATF3 was a paper on integrating single-cell data across species. Nineteen of twenty probe genes returned the same zebrafish methods paper."* Screen: **FIG 4**. |

> ### Pre-empt **#1** in the close.
> **Ten of fourteen evaluations negative.** Saying "Ten of fourteen came back negative" defuses it before it is asked. If a judge raises the held-out failure first, everything after it reads as damage control.

## Cut — answer live if asked, do not narrate

RPE1 24.2% coverage collision · tier detail · Sanger KY and scbench (not done, claim nothing) · myeloma anchor (never reached) · essentiality null (−0.021, p=0.90 — only if asked).

## Timing — MEASURED, not estimated

**409 spoken words. At 150 wpm that is 2:43**, which leaves only about fifteen
seconds for the two commands to run and the pauses to land. It fits under three
minutes and it does not fit comfortably, so rehearse it with the commands
actually running rather than by reading the words — and if you are a slow
speaker, take cut 1 below before you start rather than mid-talk.

| Beat | Words | At 150 wpm |
|---|---:|---:|
| Open, the problem | 41 | 0:16 |
| 1 The finding | 82 | 0:32 |
| 2 LIVE audit | 116 | 0:46 |
| 3 LIVE rerank | 102 | 0:40 |
| Close | 68 | 0:27 |
| **Spoken total** | **409** | **2:43** |
| Commands running + pauses | — | ~0:15 |

Recount after any edit:

```bash
.venv/bin/python -c "import re,pathlib;t=pathlib.Path('docs/DEMO.md').read_text().split('# RUNNING THE LIVE BEATS')[0];print(sum(len(re.findall(r'\\S+',q)) for q in re.findall(r'\\*\\*\"(.+?)\"\\*\\*',t,re.S)),'words')"
```

## If you are over time, cut IN THIS ORDER

**Decided now so nobody has to decide it live.** Each line says what it costs.

| # | Cut | Saves | What you lose |
|---:|---|---:|---|
| 1 | **The install line** — prefix with `PYTHONPATH=` instead | ~0w · 10s | Nothing spoken. Buys back the slowest part of the demo and costs the audience nothing. Take this one first. |
| 2 | **Beat 1's second paragraph** — the crime-count analogy | 45w · 18s | The one line that makes a statistician's point land for a biologist. Cut it only for an audience that already knows what a competitive test is. |
| 3 | **Beat 2's percentile half** — "Then the part I care about…" | 41w · 16s | The reference distribution, which is the answer to "is 46% a lot?". Keep it if there is any chance of that question being asked. |
| 4 | **Beat 3's refusal paragraph** | 56w · 22s | The reason this is not a candidate-list generator. **Never cut this and the close both** — one of them has to carry the scope limit. |

**Never cut:** the open, either live command, or the close. The close carries
"ten of fourteen", the −0.019 scope limit, and the anti-drift test, and those are
the three things the talk exists to leave behind.
