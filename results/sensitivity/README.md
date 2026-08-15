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

---

# Second post-freeze check — the VIF identity (also NOT pre-registered)

**Run 2026-08-15, evening. Prompted by an external reviewer session's
observation, then verified here by a second, independent implementation.
The two implementations were written without reading each other and agree.**

## The observation

Our two dominant features are exactly the two terms of the variance-inflation
factor for a competitive gene-set test:

    VIF = 1 + (m − 1) · ρ̄

with *m* = set size (`n_present`) and ρ̄ = mean inter-gene correlation
(`coherence`). Wu & Smyth derived this analytically in 2012 (*Camera*, Nucleic
Acids Research 40(17):e133, doi:10.1093/nar/gks461): a set-level test that
ignores inter-gene correlation is variance-inflated by this factor, and
declares more hits for larger, more correlated sets **regardless of biology**.

## The result (`vif_camera.json`)

| Model | adj R² |
|---|--:|
| **log₁₀(VIF) alone — one derived quantity** | **0.7257** |
| all six features (pre-registered upper bound) | 0.7511 |
| log VIF + the other four features | 0.7536 |
| VIF with coherence flattened to its median | 0.4629 |
| set size alone | 0.4538 |

One derived quantity captures **96.6%** of the six-feature model; the other
four features add **+0.028**. Spearman ρ(log VIF, R_p) = **+0.853**,
p = 3.6×10⁻¹⁵, n = 50.

## The bound, stated before anyone else states it

`coherence` is computed from the same matrix as the outcome, so **VIF inherits
the same partial circularity as the six-feature upper bound**. The comparison
rule is therefore: log-VIF (0.726) may only be compared to the **upper** bound
(0.751). The circularity-free statement is the flattened row (0.463), which
pairs with the pre-registered **lower** bound (0.561) and shows that without
coherence, VIF is barely better than size alone.

## What it means

The empirical pattern this project found in a genome-scale screen is the
pattern a 2012 statistical theory predicts analytically. We did not fit to
CAMERA; we recovered its inflation term from data. That is validation against
a standard outside this project's own reasoning — and it names the next
experiment: **re-run the sweep with a VIF-corrected set statistic and measure
how much of the size effect collapses.**
