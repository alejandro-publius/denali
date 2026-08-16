# Origins — why this project looks the way it does

Written fresh for this repository. The work that produced these conclusions is
not carried over; only what still binds the current code is written down here.

---

## Four projects died before this one

Every design choice below was bought with a failure. Stating them is not
throat-clearing — the demo opens with this, because a team that can show what it
killed is making a different kind of claim than one that can only show what
worked.

**A cross-paper conflict engine.** The idea was to find where published papers
contradict each other at scale. It produced contradictions, but they were
parsing and retrieval artifacts rather than disagreements between authors. Two
pre-set kill conditions fired. **Lesson that survived: a discovery engine that
cannot distinguish its own bugs from its findings is a bug generator.**

**A figure-to-value certifier.** The thesis was that a number read off a
published figure could be admitted as evidence if axis calibration and an
aggregate invariant both checked out. Our own measurements falsified it —
aggregate invariants do not constrain individual values, because errors cancel.
A screen of 500 real papers then found only ~5% state a quantity the method
could test at all. **Lesson: measure whether your instrument has anything to
measure before building the instrument.**

**A measurement-ontology project.** Killed on prior art, roughly 85–90% covered
by existing work. **Lesson: check whether the idea already exists before falling
in love with it.**

**A lung fibrosis program.** A pre-registered contrast in a 119-donor atlas
returned zero genes at FDR. A pre-registered rescue across four more cell
populations returned zero again — seven populations, best q = 0.124 — while the
same cells and the same code returned 481–6,532 genes on a different axis. The
machinery worked; the question had no signal in that dataset. **Lesson, and the
one that shapes this repo most: a clean null from working machinery is a
result, and it is only publishable if you wrote the criterion down first.**

Then, in this project, **three of four candidate gene programs failed their
measurability gate** before any pipeline was built.

## What that history actually bought

**Pre-registration as a habit, not a gesture.** Every threshold in this
repository was hashed and committed before the value it judges existed. When the
matrix result came back, the branch it triggered had been written down hours
earlier. That is why a negative finding here is reportable rather than
embarrassing.

**Sealing as a mechanism.** The held-out program was committed to git before the
scoring code was written. That ordering is checkable by anyone with `git log`,
and it is the only claim in this project that no amount of argument can weaken.

**Negatives kept, not buried.** Four of this project's seven evaluations came
back negative and all seven are reported. A post-freeze sensitivity check — run
because an adversarial critique demanded it, not because we planned it —
collapsed part of our own headline, and it is documented at the top of
`LIMITATIONS.md` rather than in an appendix.

**Suspicion of retrieval.** Earlier work found that semantic search ranks on
abstracts and returns plausible-looking sources that do not support the specific
claim. So when we used a literature tool here, we audited it instead of trusting
it — and it failed: 34 distinct sources across 113 genes, one review covering
half of them, and a blind 20-gene probe where 19 came back with the same
unrelated methods paper.

## Why this particular experiment

We wanted a question where the discovery step is itself an intervention, so
there is no correlation-to-causation gap to apologise for. Genome-scale CRISPRi
in K562 gives that: every row is "we switched this gene off and measured what
happened."

The known weakness, stated before we started: **K562 is a leukemia line and it
is unstressed.** A program that is not switched on in those cells cannot be
moved by anything, which is exactly what happened to our first choice. That is
recorded as a design failure in `LIMITATIONS.md` §3, not as bad luck.

## Design principles we adopted deliberately

- **Do not stop at correlation.** The output is a perturbation result or it is
  nothing.
- **Independent validation comes before the hypothesis**, not after it as a
  victory lap.
- **Expose the evidence against yourself.** Full tables, not significant rows.
  Failing controls on screen, not omitted.
- **Report several metrics, never optimise one.** The scoring here is rank-based
  with two other statistics reported alongside.
- **End with an object, not a document.** A frozen matrix, a hashed predictor,
  and a callable tool.
- **An LLM judging an LLM is not validation.** Every quantitative claim in this
  repo is produced by deterministic code and checked against an external
  standard — DepMap, MSigDB, a public gene-set catalogue, or a timestamp.


---

## One stale pointer, deliberately left alone

`src/score_k562.py` cites a document that no longer exists in this repository.
**The file is byte-frozen at sha256 `2abfdc6f…` because the held-out seal depends
on it**, and editing a comment would change the hash and void the held-out list. The
design principles it points at are the ones above.

This was caught while preparing this repository: a docstring was edited, the hash
moved, and the held-out list condition failed. The edit was reverted. **The rule worked.**
