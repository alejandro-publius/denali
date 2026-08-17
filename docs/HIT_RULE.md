# Evaluation 14 — the verdict depends on who called the hits

**Pre-registered** at [`docs/HIT_RULE_PREREG.md`](HIT_RULE_PREREG.md), sha256
`8e39c426…`, sealed at `f4b3f8d` before any value below existed. Artifacts:
[`results/hit_rule/`](../results/hit_rule/). Module: `src/hit_rule_audit.py`.

**Pre-registered claim (b) fired.**

---

## The finding

`denali audit` reads a size column and a hit column. It had never asked where the
hit column came from. Holding this project's own screen completely fixed and
changing **only the rule that turns the reversal statistic into a hit count**, the
verdict changes:

| rule | family | R² size alone | verdict |
|---|---|--:|---|
| BH q < 0.05 within program — **the published convention** | threshold | **0.4530** | **MORE SIZE-CARRIED THAN ITS OWN NULL** |
| uncorrected two-sided p < 0.05 | threshold | 0.5610 | MORE SIZE-CARRIED THAN ITS OWN NULL |
| Bonferroni p < 0.05/n | threshold | 0.5012 | MORE SIZE-CARRIED THAN ITS OWN NULL |
| fixed effect size \|u_z\| ≥ 2.0 | threshold | 0.5631 | MORE SIZE-CARRIED THAN ITS OWN NULL |
| top 2% of genes per program | quantile | undefined | **UNDETERMINED** |
| top 10% of genes per program | quantile | undefined | **UNDETERMINED** |
| top 200 genes per program | fixed count | undefined | **UNDETERMINED** |

The four threshold rules are scored against the **binomial null for their own
mapping**, not against zero, so each is above the no-biology value rather than
merely above nothing — which is what distinguishes this from the counting
arithmetic [scope limit 6](../README.md#scope-limits) warns about.

Same screen. Same 49 programs. Same size column. Only the hit-calling rule moves,
and the tool goes from **naming the confound the dominant feature of the ranking**
to **refusing to answer at all** — while saying nothing on its output about the
convention that decided it.

Within the threshold family the estimate is stable: the four rules span
**0.4530 to 0.5631**, a range of 0.1101, so the *choice of threshold* matters much
less than the *choice of family*.

## The reading this arm forbids, fixed before the numbers were visible

The three quantile and fixed-count rules produce a **constant** hit count by
construction — top 2% of 9,837 genes is 197 for every program, whatever its size.
So size cannot predict a hit count that never varies, and the R² collapses.

**That is not evidence those rankings are unconfounded.** It is evidence that this
diagnostic *cannot see* the mechanism under a rule that fixes the count. The
underlying asymmetry is untouched: a program with more measured members still
yields a more precise rank statistic, and its perturbations are still ranked
higher for that reason. A quantile rule does not remove the power difference — it
moves it out of the hit count and into the **within-program ordering**, which
`audit()` never reads.

So a near-zero R² here is **the instrument going blind, not the ranking coming
back clean**. This was written into the pre-registration precisely so the framing
could not be selected after seeing which way the numbers fell.

**This is a scope limit on denali, and it is the one this arm was built to find.**
Where a hit list was produced by taking a top N or a top percentile, denali's
audit is not applicable, and a "NOT SIZE-DOMINATED" verdict on such a list is a
false reassurance rather than a finding.

## The defect this surfaced in the shipped tool — found here, fixed at `5f10e28`

The quantile rules were *expected* to return `UNDETERMINED` — the packaged tool has
a refusal branch for exactly this case, added on 2026-08-16. On this arm's first
run they returned an all-clear instead, with a **negative R²**, which is how the
following came to light. **The table above is the corrected behaviour; the table
below is what the shipped package did until this arm ran.**

`core.py`'s `_r2()` guards the degenerate case with `ss_tot == 0` — an exact
floating-point test on a quantity that is only *mathematically* zero. Elementwise
`log10` of the same integer is not always bit-identical, so with a constant hit
column `ss_tot` lands near `9.7e-30` rather than `0.0`, the guard does not fire,
`1 - ss_res/ss_tot` divides by a denormal, and the resulting garbage is passed on
as a valid share. `audit()`'s `if not np.isfinite(share)` refusal never runs.

Measured on 49 real programs against a constant hit column:

| constant hits | ss_tot | R² | verdict |
|--:|--:|--:|---|
| 0, 1, 2, 10, 50, 100, 500, 1000 | `0.0` | nan | UNDETERMINED — correct |
| 5 | `6.0e-31` | −6.4694 | NOT SIZE-DOMINATED — **wrong** |
| 197 | `9.7e-30` | −6.1224 | NOT SIZE-DOMINATED — **wrong** |
| 200 | `9.7e-30` | −3.6531 | NOT SIZE-DOMINATED — **wrong** |
| 984 | `9.7e-30` | −3.6531 | NOT SIZE-DOMINATED — **wrong** |

**Whether the shipped tool refuses or issues an all-clear depends on the
floating-point representability of `log10(1+k)` for the caller's own hit count.**
A constant 10 refuses correctly; a constant 5 does not.

**Why it survived, which is the part worth keeping.** The refusal branch was added
after dropping an all-zero-hits table into the page runner. `k = 0` is one of the
values where `log10(1+0)` is exactly `0.0` for every element, so the exact test
fires and the branch works. The fix was therefore verified against the single
input that *cannot* expose the flaw, and then generalised to "constant hits",
which is false for most values.

That is a distinct failure shape from the four in
[`METHOD_RULES.md`](METHOD_RULES.md). Those are ways a check can be green while
testing nothing. This one is a check that **was** exercised, **did** fire, and was
confirmed on an input whose success does not extend to the class it claims to
cover. The lesson is the one this repository already states and did not apply
here: mutate across *several* inputs of the class, because one member of a class
can pass for reasons the others do not share.

**Who this reaches.** Any top-N hit list — "our top 200 hits" is an ordinary way
to publish a screen — any quantile hit definition, and, per the branch's own
comment, screen-level inputs where every set returns the same count.

Reported rather than fixed here: `core.py` was dirty in a shared checkout at the
time, and a dirty file is not this session's to edit. The session holding it
reproduced the defect independently before changing anything, confirmed it was
still live in a rewrite that had just landed, and fixed it at **`5f10e28`** using
both parts of the reported fix — degeneracy detected on the raw integer vectors
with `np.ptp`, and a scale-relative tolerance in `_r2` replacing the exact `== 0`.
Their independent reproduction found **eight** leaking values rather than the four
seen here, because the verdict vocabulary had changed in between; the mechanism was
identical. The regression test is parametrised over exactly the leaking values,
because `k = 0, 1, 2, 3, 10, 50, 127, 500, 1000` all refuse correctly *without* the
fix — so a test built on any of those would have passed against the bug.

**This arm's conclusion never depended on the defect.** With it, the count-fixing
rules issued a false all-clear; without it they return `UNDETERMINED`. Both differ
from the threshold family's verdict, so pre-registered claim (b) fires either way.
The published headline is unmoved at 0.4649.

## Why this is not a correction to the headline

**It is not, and it cannot be.** `results/frozen/matrix.csv` is not the vector the
published hit counts were computed on: `src/sweep.py` counts hits over all 11,258
perturbation rows and only then collapses to 9,837 unique target genes by each
gene's **maximum** `u_z`. Recomputing any threshold rule here therefore works on
fewer rows, an upward-shifted distribution and a different BH denominator. The
470 MB substrate that would permit the uncollapsed comparison is gitignored and
absent.

That gap was written into the pre-registration before it could be discovered, with
a kill criterion of 0.10. The published convention recomputed here returns
**0.4530** against the published **0.4649** — a gap of **0.0119**, well inside the
limit. So the collapse turns out to cost little, but **every absolute R² on this
page remains substrate-specific and none may be quoted as this project's
headline.** What this arm is entitled to is the comparison *across rules on one
substrate*, which is the comparison its question needs.

## Scope

One screen, 49 scoreable programs of 50 — one program's column is entirely
non-finite and cannot be thresholded or ranked under any rule, so it is excluded
rather than imputed, and counted in the artifact rather than silently dropped.
Establishes that the rules differ on a real screen; not how they compare in
general. Writes `results/hit_rule/` only, never `results/frozen/`. No gene, gene
set or publication is named as a finding. No claim that any hit-calling convention
is wrong — thresholding and quantile-cutting are both standard and both
defensible.

## Reproduce

```bash
.venv/bin/python -m src.hit_rule_audit
```
