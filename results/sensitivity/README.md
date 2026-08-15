# Post-freeze sensitivity check — NOT pre-registered

**Run 2026-08-15, after the 6:30 PM hard freeze.**

**Prompted by an adversarial self-critique that named this as the project's
weakest point. It was not in the plan.** That sequence is part of the honest
record and is stated here rather than smoothed over.

This directory is deliberately **outside `results/frozen/`**. Nothing here
replaces, revises or reweights the pre-registered primary result. **The
pre-registered range, adjusted R² 0.561–0.751, stands exactly as reported.**

---

## The question

Our six "measurability" features are not all measurements. Three of them —
`n_present`, `frac_present`, `coherence` — are properties of **how the gene set
was constructed**. Only three are properties of the measurement: `expr_ratio`,
`sd_ratio`, `essentiality_density`.

If the finding is carried by the construction features, then "measurability
dominates" is the wrong attribution.

## The result — it collapses

| Model | features | adj R² |
|---|---:|---:|
| All six — **the pre-registered primary** | 6 | **0.751** |
| Outcome-independent five (drops `coherence`) | 5 | 0.561 |
| **Measurement only** — `expr_ratio`, `sd_ratio`, `essentiality_density` | 3 | **0.152** |
| **Set construction only** — `n_present`, `frac_present`, `coherence` | 3 | **0.697** |
| Set size alone | 1 | 0.465 |

Measurement-only coefficients: `expr_ratio` −0.042 (p=0.87), `sd_ratio` +0.285
(p=0.11), `essentiality_density` +0.532 (p=0.039).

## What this means, stated plainly

**Our headline attributed the variance to measurement. It is carried by gene-set
construction.** Three construction features alone reach 0.697; three measurement
features alone reach 0.152. Set size by itself beats all three measurement
features combined, three times over.

**The corrected reading:** how many knockdowns appear to move a program is
mostly a function of how the program was defined — chiefly how many genes are in
it — rather than of how well those genes were measured, and not of the program's
biology.

The original claim is not rescued by this being "still interesting". It was
wrong about mechanism, and the correction was found by an adversary, not by the
plan.

## What survives and what does not

**Survives.** Apparent reversibility is largely not biology. The pre-registered
statistic, its threshold and its verdict were fixed before the sweep and are
unchanged. Every other finding — the gate being wrong 20 of 50, the held-out
failure, the essentiality null, the retrieval audit — is untouched.

**Does not survive.** The word *"measurement"* in the headline. And the implicit
suggestion that better instrumentation would change the answer: it would not,
because the dominant term is a property of the gene-set catalogue.

## Reproduce

```bash
.venv/bin/python -m src.sensitivity_stripped   # < 1 s
```

Raw values: `stripped_model.json`.
