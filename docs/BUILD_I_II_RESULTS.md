# Build I + II results — 2026-08-15

**The primary program failed. The held-out program succeeded.**
That sentence is the result, and the ordering of the commits is what makes it
credible rather than convenient.

---

## Headline

| | Primary: UPR | Held-out: cholesterol |
|---|---|---|
| Held out before scoring? | no (chosen after the gate) | **yes — commit `63596b5`** |
| Top hit | MCM4 (DNA replication licensing) | **SREBF2 (master cholesterol TF)** |
| Top hit rank | 1 / 11,258 | **2 / 11,258** |
| Canonical regulators recovered | **no** — PERK/IRE1/XBP1 at q≈0.8–1.0 | **yes, both tails, correct sign** |
| Top-50 essentiality enrichment | 4.09× (p<0.001) | 3.32× (p<0.001) |
| Perturbations at q<0.05 | 517 | 773 |
| Nonsense control | 0 survive | 0 survive |

## Framing decision (Section 3)

Eight framings generated, then criticised. **The obvious answer — split output
into essential-and-replicable vs non-essential-single-line — was rejected**: it
presents the smaller tier as trustworthy when that tier is precisely the
essentiality-confounded one.

Guide-pair replication inside K562 was recommended instead, then **killed by a
60-second check**: only 738 genes carry separate `P1`/`P2` rows (8,866 are
already collapsed to `P1P2`), giving 7.5% coverage — worse than RPE1's 24.2%.

**Settled: two-tier output with an essentiality-matched null.** Tier boundaries
are drawn by DepMap fitness, not by RPE1 coverage. RPE1 is the cross-cell-type
generalisation check with a stated denominator, never "the replication arm".

## The collision, quantified

The 24.2% headline understated it badly:

| | RPE1 coverage |
|---|---:|
| Essential genes (Chronos < −0.5) | **94.1%** |
| Non-essential genes | **11.3%** |

The replication arm covers almost exclusively the genes the toxicity filter
flags. SREBF2, MYLIP, INSIG1 and LDLR — the most interpretable hits — are all
**NOT COVERED**.

## Tiers (identical for both programs; they partition perturbations, not hits)

| Tier | n |
|---|---:|
| T1 reversal not explained by fitness | 7,857 |
| T2 reversal confounded by essentiality | 1,541 |
| T3 no fitness data | 439 |

## Divergence table (Section 6)

113 UPR program genes, cross-referenced against their own knockdown scores:

⚠ **Reframed 2026-08-15 to program level.** The original table issued 113
per-gene verdicts, which −0.019 concordance does not support. Counts retained,
verdicts withdrawn.

| Member class (COUNTS, not verdicts) | n |
|---|---:|
| Never perturbed in the screen | **12** |
| Perturbed, no detected move | **90** |
| Perturbed, moved the program | 11 |

**🔴 12 of 113 UPR program genes were never perturbed in the screen:**
CCL2, CKS1B, DNAJA4, ERO1A, H2AX, IARS1, IFIT1, IGFBP1, SKIC3, SRPRA, TARS1, WFS1.

DISAGREES by citation count: ATF3 (11,270), HERPUD1 (11,270), HSPA5 (9,217,
q=0.061), EIF4EBP1 (6,836), CALR (5,207), **EIF2AK3/PERK** (5,207), **ERN1/IRE1**
(4,713, u_z=0.001), **XBP1** (4,317). AGREES (11) is dominated by translation
initiation and the RNA exosome, not UPR biology.

## Controls

| Control | Result |
|---|---|
| **Nonsense program** (41 random genes, seed 20260815, pre-committed) | **0 perturbations at q<0.05**, vs 517 (UPR) / 773 (cholesterol). ✅ The method does not manufacture signal. |
| **Known-regulator recovery, cholesterol** | SREBF2 rank 2, SCAP 27, MBTPS2 49, MBTPS1 56, MYLIP 57 (all suppressors). INSIG1 11,230, HMGCR 11,229, LDLR 11,194, HMGCS1 11,095 (all activators-on-loss). **Correct sign at both tails.** ✅ |
| **Known-regulator recovery, UPR** | ATF4 rank 134 (1.2%) is the only recovery. ATF6 14.1%, XBP1 24.9%, ERN1 49.7%, PERK 61.7%. ❌ |
| **Guide-pair concordance** (738 genes, separate P1/P2) | **Spearman −0.019.** Holds at every effect-size cut: −0.001 (n=339), +0.029 (n=190), +0.048 (n=93), −0.076 (n=43). ❌ **The most damaging result of the night.** |
| **Essentiality-matched null** | Top-50 essential fraction 0.640 vs 0.157 overall = 4.09×, empirical p<0.001 over 1,000 draws. ❌ for UPR. |

## Section 9 — the generalization run

Pipeline run **unchanged** on the held-out program. No threshold moved, no gene set
swapped, no re-specification.

**SREBF2: rank 2/11,258, u_z +7.06, Chronos −0.024 (not essential), Tier 1,
NOT COVERED in RPE1.**

Both tails mechanistically correct: knocking down SREBP-pathway *activators*
suppresses the program; knocking down *INSIG1* (the canonical negative regulator)
or the sterol-synthesis enzymes activates it by feedback. A fitness artifact does
not produce correct signs at opposite ends of a ranking.

### Expert comparison

**UPR top 5** — MCM4, DUT, SEH1L, ORC5, EIF3D. An expert names XBP1, ATF6, IRE1,
PERK, ATF4, BiP, CHOP. **Overlap: zero.** With the 4.09× essentiality enrichment,
**this divergence is a failure, not a discovery.**

**Cholesterol top 5** — SREBF2 and SCAP, then three genes not canonical to the
pathway. An expert names SREBF2, SCAP, INSIG1, HMGCR, LDLR. **Top 2 match
exactly**; INSIG1/HMGCR/LDLR are recovered at the opposite tail with correct sign.

⚠ **The three non-canonical entries are NOT named as candidates and no claim is
made for them.** Guide-pair concordance is −0.019, so a gene-level call at those
ranks is not reproducible. See `SCOPE_STATEMENT.md`. The pipeline's demonstrated
capability is **pathway-level**: 11 of 17 canonical members in the extreme 10%,
binomial p = 7.0 × 10⁻⁸.

## Section 8 — scbench: ABANDONED, no number

Cloned. Not run. Three blockers, none fixable tonight: `ANTHROPIC_API_KEY` unset,
no Latch credentials (every eval's data is behind `latch://` nodes), `scbench`
not installed. **We have no scbench score and must not claim one.**

Worth noting without claiming: DE01's primary trap is testing whether the agent
pseudobulks with donor as covariate rather than treating ~1,300 cells as
independent (t-test → 3,194 DEGs; truth 1,150 ± 350). That is exactly this
project's founding rule in `METHOD_RULES.md`.

## Paperclip — RE-RUN after authentication, and it changes the claim

The user authenticated Paperclip mid-session, so step 1 was re-run against the
real source (`src/paperclip_program.py`, output
`results/discovery/upr_program_paperclip.csv`). Both columns are kept side by
side: `paperclip_*` for evidence, `epmc_*` for the count metric. Paperclip's
`search` does not expose a citation count, so citation-count ranking still uses
the Europe PMC column and is labelled as such.

**113/113 genes returned a citation. 0 errors.** But the evidence chain is
weaker than "one citation per gene" implies, and this is a finding:

| | |
|---|---:|
| Distinct PMC IDs across 113 genes | **34** (Europe PMC gave 75) |
| Genes served by ONE review — *"When Proteins Go Berserk"* | **57 of 113** |
| Citations used for exactly one gene | 25 |
| Top hits whose **title actually names the gene** | **14 / 113** |
| Paperclip top-hit year range | **2024–2026 only** |

**Interpretation, stated plainly.** One-shot semantic search returns *a recent
review that plausibly mentions the gene*, not the evidence that establishes the
gene's role. ATF6's foundational papers are from ~2000; Paperclip's top hit for
ATF6 is a 2025 hearing/vision-loss syndrome paper. For 14 genes it produced
genuine gene-specific evidence (ATF4, ATF6, BAG3, CHAC1, DDIT4, DNAJC3 among
them); for the rest it produced a pointer to a review.

This reproduces a standing rule in `METHOD_RULES.md` — *semantic retrieval
ranks on abstracts; citation chaining can outperform it on targeted corpora.*
The fix is `paperclip citation-explorer` / repo-scoped chaining, not a bigger
one-shot query. **Not done tonight.** Do not describe the pipeline as producing
a per-gene evidence chain until it does.

## Other substitutions and shortfalls — recorded, not buried

1. **Europe PMC remains the source for citation COUNTS**, because Paperclip
   `search` does not return them. Labelled in every table.
2. **`citedByCount` is a paper property, not a gene property.** 75 distinct PMIDs
   cover 113 genes. `hits` is the primary literature metric; sanity check passed
   (ATF6, ATF4, XBP1, HSPA5 top it).
3. **Sanger KY was NOT used.** Section 7 specified Avana + KY cross-library
   agreement; only the merged `CRISPRGeneEffect.csv` was used. **Not done.**
4. **Plugins load next session.** The five life-sciences plugins and
   SciAgent-Skills were installed and enabled but were not active this session,
   so `single-cell-rna-qc` / `scvi-tools` were not invoked; scverse practice was
   followed manually.
5. **A denominator bug was found and fixed mid-run** — `avg_rank` spans 11,258
   perturbation rows, not 9,837 unique targets. Control-1 percentages printed
   >100% before correction.
6. **SciAgent-Skills has no CRISPR-screen skill.** 149 skills; nothing covers
   perturbation screen analysis.

## Open risks

1. **Guide-pair concordance ≈ 0 kills per-gene nomination.** Pathway-level claims
   survive; an arbitrary single gene does not.
2. **K562 has no ER stress**, so the UPR was never engaged. The gate tested
   measurability, not *engagement* — that distinction was missing from the
   pre-registration and is the attack to pre-empt.
3. **SREBF2 is a rediscovery.** It validates the method; it is not a discovery.
4. **Transcriptional reversal is not phenotypic reversal.** Unaddressed.
5. **The most interpretable hits have no replication** — SREBF2, MYLIP, INSIG1,
   LDLR are all outside RPE1's 24.2%.
6. **Mean Chronos across 1,178 lines** is the essentiality statistic; a
   K562-specific column is the correct comparator and would move tier calls.
