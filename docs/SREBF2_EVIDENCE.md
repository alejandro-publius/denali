# SREBF2 evidence package

The headline. Built to survive interrogation, not to look good.

---

## 1. Methods note on ordering

Thresholds and the held-out program list were committed before the corresponding
results existed, and the scorer is byte-frozen at sha256 `2abfdc6f…`. See
`docs/PRIOR_WORK.md`. **This is provenance, not the argument.** What follows is.

## 2. Rank distribution — the claim

Rank 2 alone is a lucky-hit story. **The pathway clusters**, which is not.
This is the entire basis for treating the result as a working control.

All **17/17** canonical sterol-pathway members were present in the screen.

| Gene | Rank | %ile | u_z | Tier | Role |
|---|---:|---:|---:|:--:|---|
| **SREBF2** | **1** | 0.01% | +7.06 | **T1** | master TF, cholesterol synthesis |
| SCAP | 3 | 0.03% | +4.82 | T2 | sterol sensor, escorts SREBP |
| MBTPS2 | 7 | 0.07% | +3.74 | T1 | S2P protease, cleaves SREBP |
| MBTPS1 | 11 | 0.11% | +4.00 | T2 | S1P protease, cleaves SREBP |
| MYLIP | 12 | 0.12% | +4.72 | T1 | IDOL, degrades LDL receptor |
| FDFT1 | 142 | 1.44% | +3.16 | T1 | squalene synthase |
| INSIG2 | 1,130 | 11.5% | +1.76 | T1 | retains SREBP in ER |
| NR1H2 | 1,351 | 13.7% | +1.75 | T1 | LXR-β, efflux |
| NR1H3 | 1,526 | 15.5% | +1.71 | T1 | LXR-α, efflux |
| DHCR7 | 4,768 | 48.5% | −0.58 | T1 | synthesis enzyme |
| SREBF1 | 4,933 | 50.2% | −0.08 | T1 | sister TF, mostly fatty acid |
| MVD | 5,632 | 57.3% | −0.55 | T1 | mevalonate pathway |
| HMGCS1 | 9,722 | 98.8% | −3.74 | T2 | synthesis enzyme |
| SQLE | 9,740 | 99.0% | −5.84 | T1 | squalene epoxidase |
| LDLR | 9,795 | 99.6% | −5.61 | T1 | LDL receptor, uptake |
| HMGCR | 9,814 | 99.8% | −7.04 | T2 | rate-limiting synthesis enzyme |
| INSIG1 | 9,815 | 99.8% | −5.53 | T1 | retains SREBP in ER |

> **11 of 17 land in the extreme 10% of a 9,837-gene ranking.
> Expected by chance: 1.7. Binomial p = 7.0 × 10⁻⁸.**

## 4. Both-tails sign correctness — one number

Expected direction was assigned **from biology**, then checked against position.
Activators of the program → knockdown suppresses it → top. Negative regulators
and synthesis enzymes → knockdown depletes sterol or releases SREBP → program
rises → bottom.

> ## **11 / 14 = 79% sign-correct**

**Correct (11):** SREBF2, SCAP, MBTPS1, MBTPS2, MYLIP (top) · INSIG1, HMGCR,
HMGCS1, SQLE, MVD, LDLR (bottom).

**Wrong (3), disclosed:** INSIG2 (expected bottom, landed 11.5%), FDFT1 (expected
bottom, landed 1.4%), DHCR7 (expected bottom, landed 48.5% — essentially no
signal).

79% is the honest number. A fitness artifact does not produce correct signs at
**opposite** ends of one ranking; three misses are what a real, noisy biological
readout looks like.

## 5. What SREBF2 is, stated plainly

**SREBF2 encodes SREBP-2, the master transcription factor for cholesterol
biosynthesis and LDL-receptor expression.** It is the textbook answer. Any
lipid-metabolism researcher would name it in the first breath.

> ### This is a RECOVERED KNOWN ANSWER, not a discovery.
>
> It is the positive control that says the ranking works. We claim no novelty for
> it. We name no novel gene anywhere — see `SCOPE_STATEMENT.md`.

The scientific content is not "SREBF2 matters." It is: **an untuned pipeline,
pointed at a program held out before its own code existed, put the right gene
first and got the sign right at both ends of the list.**

## 6. Rank frames — read this before quoting a number

Two denominators exist and both are correct:

- **`rank` in `results/frozen/program_b_scores.csv`: over 9,837 unique genes.**
  SREBF2 = **rank 1**.
- **`average_rank`: over 11,258 perturbation rows** (some genes tested twice).
  SREBF2 = **rank 2**.

> ## CANONICAL FRAME: **rank 2 of 11,258 scored perturbations.**
> Use this everywhere — report, demo, page, captions. State the denominator when
> you say it: 11,258 is larger than 9,837 because some genes are targeted twice.
> `rank 1 of 9,837` is the same result in the unique-gene frame and is retained
> here for completeness only. **Do not quote it; do not mix them.**

An earlier draft of Build II reported percentages using the wrong denominator;
that error was found and corrected.

## 7. What this does not show

- **Not** that SREBF2 was discovered here.
- **Not** that any individual gene call is reproducible — guide-pair concordance
  is −0.019.
- **Not** phenotypic reversal. Transcriptional movement only.
- **Not** replicated in a second cell type: **SREBF2, MYLIP, INSIG1 and LDLR are
  all NOT COVERED in RPE1.**
- **Not** free of essentiality enrichment: program B's top 50 is 3.32× enriched.
  SREBF2 itself is not essential (Chronos −0.024, Tier 1), which is why it
  survives the filter.

## 8. ⚠ TIER CAVEAT — found in the Section 8 check, after this doc was published

Tiers above use **mean DepMap Chronos across 1,178 cell lines**. Re-checked
against **K562-specific** Chronos (`ACH-000551`), the line we actually scored in:

| Gene | Mean | K562 | Tier above | Under K562 |
|---|---:|---:|:--:|:--:|
| **MBTPS2** | −0.492 | **−0.632** | T1 | **T2** |
| **LDLR** | −0.215 | **−0.568** | T1 | **T2** |

**Two tier labels in the table above are wrong for K562.** Corrected here rather
than silently edited, because the table was already committed and pushed.

**The headline is unaffected and slightly stronger:** SREBF2 is **−0.024 by mean
and +0.029 in K562** — not essential by either measure, with more margin in the
relevant cell type. Top-50 essentiality enrichment is unchanged (26 vs 25 of 50),
so the 3.32× figure stands. Repo-wide, 555 of 9,333 genes (5.9%) disagree between
the two measures.

**Not yet done:** re-tiering all 9,837 rows on K562-specific Chronos. The frozen
files still use the mean. If the demo shows a tier for MBTPS2 or LDLR, say
"essential in K562" for both.
