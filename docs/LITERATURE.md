# Evaluation 11 — does the field say so?

**PRE-REGISTERED** as to its claim, power rule and search terms
(`docs/LITERATURE_PREREG.md`, sha256 `165d91a2…`, committed at `b0c5e35`
**before this arm produced anything**). The arm itself is **post-freeze**, like
evaluations 6, 8 and 10, and says so here.

Evaluation 10 measured the size confound across 1,272 published screens and
found a field median of **0.224**. It could not ask whether anyone had noticed.
This asks exactly that, of the same publications, and nothing else.

## Result

| | | |
|---|--:|--:|
| Publications behind the corpus arm | **187** | |
| Resolved to full text in PubMed Central | **111** | **59.4%** |
| **Tier A — mention set size explicitly** | **4** | **3.6% of resolved** |
| Tier B — competitive-test machinery | 16 | 14.4% of resolved |
| Either tier | 20 | 18.0% of resolved |

**The pre-registered power rule did not fire.** The floor was 60 resolved
publications and 111 resolved, so the fractions carry a verdict rather than a
shrug.

**Branch (b) fired.** Tier A came in far below the 50% threshold that would have
made our framing wrong. Of the publications whose screens we audited, **96.4% do
not mention gene-set size anywhere in their full text** — not in the methods, not
in the limitations, nowhere a regex over the whole document would find it.

## The check that makes this a finding rather than a bug

**A near-zero hit rate and a broken regex look identical in the output.** That is
the failure this project has already hit three times, so Tier A is run against
three gene-set-enrichment **methods** papers that certainly discuss set size,
found by topic search and not chosen for matching. All three fire:

| control | Tier A patterns matched |
|---|---|
| Simultaneous enrichment analysis, unifying self-contained and competitive methods | `pathway size` |
| Avoiding the pitfalls of gene set enrichment analysis | `gene-set size`, `set size`, `larger gene sets` |
| A general modular framework for gene set enrichment analysis | `gene-set size`, `set size`, `number of genes in the set` |

`.venv/bin/python -m src.literature_audit --control` reruns it and exits nonzero
if any control stops matching. The control is in the script rather than in
somebody's shell history, for the same reason every other guard here is.

## What this does and does not say

**It measures mention, not understanding.** A regex match means the topic appears
in the text. It does not mean the paper handled it correctly, and a paper that
mentions set size while getting it wrong counts as a match here. Reading 111
papers properly is not something we did, and claiming the stronger version would
be the exact overreach this project exists to detect.

**The denominator is PubMed Central, not the literature.** 111 of 187 resolved,
so **40.6% of the publications could not be checked at all**. Open access is not
a random sample of publishing: it skews recent, better-funded and more
methods-forward — and if anything that biases *toward* finding size discussion,
which makes 3.6% a ceiling on the true rate rather than a floor. That direction
is worth stating because it is the one that does not flatter us.

**Tier B is the more interesting 14.4%.** Those are papers using or citing
competitive-test machinery — CAMERA and its relatives, inter-gene correlation,
variance inflation — which exists *because* of this confound. They were
pre-registered to be reported as uninformative above 90%, on the grounds that a
near-total rate would be matching boilerplate. At 14.4% that rule did not fire,
so the number stands: roughly one publication in seven reaches for the right
machinery, and roughly one in twenty-eight names the problem.

**No publication is named.** Aggregate counts only, here and everywhere else. The
existing corpus scope invariant fails the build if a PMID appears on any rendered
surface, and this arm inherits it.

## Why it is not a stronger claim than it looks

The obvious overstatement available here is *"the field is unaware of a confound
that costs it half its rankings."* We are not saying that, for three reasons
stated before the numbers were seen:

1. The confound is **documented** — CAMERA measured the mechanism in 2012, and
   this arm's own Tier B shows people using it. What is missing is discussion in
   the papers that *report the affected rankings*, which is a narrower claim.
2. **Not mentioning something is not the same as not knowing it.** Methods
   sections are short and journals cut them.
3. Our own headline is **atypical in magnitude** — evaluation 10 put denali near
   the 73rd percentile of publications, not the 99th. The mechanism is universal;
   our screen shows it unusually clearly.

## Reproducing

```bash
.venv/bin/python -m src.literature_audit            # the full arm, ~25 min
.venv/bin/python -m src.literature_audit --control  # the positive control alone
```

**This is a live-index step and is deliberately not in `make all`**, for the same
reason `make retrieval` is not: Paperclip's index moves, so the counts here are a
dated observation from **2026-08-15**, not a reproducible number. Re-running it
later will move them, and that instability is a property of literature search
rather than a defect in this arm.

The query set is the 187 PMIDs in `results/corpus/corpus_per_screen.csv`, which is
**disjoint from FIG 4's 20 probe genes** — running this cannot move any number
that figure reports.

Outputs: `results/literature/literature_audit.json`,
`results/literature/literature_per_publication.csv`,
`results/literature/positive_control.json`.
