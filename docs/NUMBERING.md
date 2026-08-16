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

---

# Branch disposition, 2026-08-16

Eleven branches existed; the repo now carries `main` alone. Recorded here so a
deleted branch is a decision with a reason rather than a gap.

| branch | tip | disposition |
|---|---|---|
| `adamson-arm` | `816c500` | **merged** — evaluation 9 |
| `corpus-arm` | `6edd2b0` | **merged** — evaluation 10, renumbered from 8 |
| `fulcher-prior-art` | `09fb5e0` | **merged** — kept as the base of §2b |
| `fulcher-landscape` | `a36ca0e` | **folded in**, then deleted — its three best points grafted onto §2b; merging both would have cited Fulcher twice in two voices |
| `validation/external-gallery` | `54469a3` | **merged** — seven external screens |
| `copy/page-accuracy` | `8e94b98` | **merged** — fonts and design invariants kept, its stale copy discarded |
| `offtarget-arm` | `a372aa2` | **deleted, not merged** — a parallel preservation of the same arm already on `main` (identical JSON, script, both CSVs). Three of its invariants were ported first |
| `style/denali-brand` | `d963f30` | **deleted, not merged** — see below |
| `frontend-demo-layer` | `f9054c6` | deleted — 0 ahead, fully contained in `main` |
| `loop-diagram` | `7aa1cec` | deleted — 0 ahead, fully contained in `main` |

**Why `style/denali-brand` was not merged.** Its work *is* on `main`: the brand
palette (`#1B2A4A`, `#2EC4A0`), all four inlined webfonts, and the mark arrived
via `copy/page-accuracy`, which reimplemented them on a far newer base — renaming
`--teal` to `--accent` and documenting the radius decision. The branch itself sat
42 commits behind and still contained the pre-`60fd349` hero and five hardcoded
metric tiles (`7/4/2/1/0`) that the tracer now derives from the README findings
table. Merging it would have reverted the headline and reintroduced hand-typed
counts — the exact failure `60fd349` existed to remove. Its tip `d963f30` remains
recoverable by SHA if any of that judgement turns out to be wrong.
