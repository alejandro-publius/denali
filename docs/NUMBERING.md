# Evaluation numbering — the decision record

Two branches independently claimed **evaluation 8**. This file records how that
was resolved and why, so the next person does not have to reconstruct it from
merge commits.

## The collision

| claimant | work | where it was |
|---|---|---|
| `main` (67c5cfe) | off-target nomination — CHANGE-seq / CRISPRme | merged, published, hosted |
| `corpus-arm` (78ca156) | the headline against 1,272 published screens | one commit on a branch |

Both were built the same night, in different sessions, against a README whose
findings table ended at 7.

## The decision

**Evaluation 8 is the off-target arm. The corpus arm is renumbered.**

Final assignment, once the full merge queue was known:

| # | arm | why this number |
|---|---|---|
| 8 | off-target — CHANGE-seq / CRISPRme | already on `main`, published and hosted |
| 9 | Adamson engagement arm | merged next |
| 10 | corpus — 1,272 published screens | merged after Adamson |

An earlier draft of this file assigned the corpus arm 9, written before the
Adamson arm entered the queue. The rule did not change — arrival order did.

Two reasons, in order:

1. **Chronology.** The off-target arm reached `main` first. The numbering follows
   the order findings landed, which is the only ordering that stays stable as more
   arms are added.
2. **Churn.** By the time the collision surfaced, "eight evaluations" was restated
   in the README intro, the findings table, the plain-language section, `CLAUDE.md`,
   `METHOD_RULES.md`, `ORIGINS.md`, `MORNING_HANDOFF.md`, `DEMO.md`, `app.py` and
   `index.html`, and it was live on the hosted page. Renumbering the published arm
   to promote an unmerged branch would have rewritten all of that to no benefit.

Number by arrival, not by importance. The corpus arm is arguably the more
consequential result — it is the one that says our headline is atypical of the
field — and it is still evaluation 9.

## What enforces it

`tests/test_frozen_invariants.py` parses the README findings table as the single
source of truth: rows must be numbered `1..n` with exactly one verdict each, and
every prose restatement of the count is checked against it. A future collision
fails the build rather than shipping two arms with the same number.

Adding an arm therefore means: append the row, and let the guard tell you which
prose has gone stale.
