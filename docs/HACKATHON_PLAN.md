# Hackathon plan — Track A, "Build an AI Scientist"

**Program: proteostasis, UPR arm.** Selected 2026-08-14 after the Candidate 1
gate passed 3/3 (`GATE_C1_RESULTS.md`, commit `280c626`).

| | |
|---|---|
| Check-in | **08:30 AM** |
| Submission deadline | **Sunday 10:45 AM** |
| Real build time | **~10 hours** |

**The science lands before the demo. The demo is built Sunday over frozen tables.**

---

## Pipeline

| # | Step | Purpose | Notes / risk |
|---:|---|---|---|
| 1 | **Paperclip builds the proteostasis gene set, one citation per gene** | This is Track A's evidence-gathering clause — it is what makes this an *agent* rather than a script | ⚠ `PAPERCLIP_API_KEY` **not set**. Fallback: ship the gate's `HALLMARK_UNFOLDED_PROTEIN_RESPONSE` (113 genes, already committed) and label it uncited |
| 2 | **Score all ~9,823 K562 CRISPRi knockdowns for opposition to the program** | The discovery step. Pseudobulk, classical statistics | Substrate on disk and md5-verified. No neural model in the scoring path |
| 3 | **RPE1 replication arm** | Second cell type, independently screened | ⚠ **Coverage denominator stated on screen.** Only 2,381/9,823 = **24.2%** of K562 targets exist in RPE1, and that subset is the *essential-gene* subset, not random |
| 4 | **DepMap 24Q4 essentiality filter — Broad Avana AND Sanger KY** | Flag any hit that only scores because it kills the cell | Two independent libraries = real external adjudication. ⚠ Collides with step 3: the genes RPE1 can replicate are disproportionately the ones this filter flags |
| 5 | **Proto on Modal — structure of the top hit** | Structural context for the top-ranked recovered known gene | Modal credits arrive day-of. Not on the critical path |
| 6 | **Tamarind Bio — binder design if there is a pocket** | Only if step 5 yields a pocket | Conditional. Drop without hesitation if time is short |
| 7 | **Biohub ESMC SAE — frozen-model features, no retraining** | Interpretability layer on a frozen model | Mirrors the KScope winning pattern exactly (see `WINNING_PATTERNS.md` §9) |
| 8 | **Benchling MCP write-back** | Register the target with its evidence chain | OAuth, no key needed |
| 9 | **Expose the scored matrix as an MCP server** | The durable, reusable artifact | One tool: query by program → ranked genes with reversal score, RPE1 rank **or "not covered"**, essentiality flag. Proven winning artifact (`WINNING_PATTERNS.md` §8) |
| 10 | **Streamlit page, Sunday, over frozen tables** | The demo | Step timeline; target card; next-four table **including at least one gene the filter killed** |

### Non-negotiables inside the pipeline

- Steps 5–7 are **optional**. Steps 1–4 and 9–10 are the spine. If time
  compresses, cut from the middle, never from the spine.
- The "next four" table **must** include a killed gene. Showing the filter
  working is stronger evidence than showing four survivors.
- Report **several metrics, not one headline number** (see `WINNING_PATTERNS.md` §7).
- Every screen that shows an RPE1 rank shows its denominator.

---

## Schedule

| Block | Time | Work |
|---|---|---|
| Check-in | **08:30 AM** | — |
| **Build I** | **1:00 – 3:30 PM** | Paperclip gene set (step 1); K562 scoring (step 2) |
| **Build II** | **3:30 – 6:30 PM** | RPE1 arm (step 3); DepMap filter (step 4) |
| **Build III** | **7:15 – 9:45 PM** | Hero figure; adversarial self-attack; **launch any long job at the 9:45 PM checkpoint** |
| **Sunday** | **9:00 – 10:45 AM** | MCP server (step 9); Streamlit page (step 10); clean-clone reproduction check; **submit** |

**9:45 PM is a hard checkpoint.** Anything that needs to run overnight starts
there or does not start.

**Sunday morning is 105 minutes for four items.** The reproduction check is not
optional padding — it is the claim that the result is real. If something must be
cut Sunday, cut demo polish, not reproduction.

---

## Open risks — recorded, not hidden

1. **Transcriptional reversal is not phenotypic reversal.** This is the most
   likely judge attack. A knockdown that moves the UPR signature has not been
   shown to rescue any cellular or disease phenotype. State this on the slide
   before a judge states it for us; do not let the demo imply otherwise.
2. **The top hit may be a known upstream regulator.** Rediscovery is a real
   possibility. If the top hit is a canonical UPR regulator, say so plainly and
   treat it as a positive control that validates the method — do not present a
   rediscovery as a discovery.
3. **Track A is the most crowded track at this event.** Differentiation has to
   come from the evidence chain and the honest nulls, not from novelty of concept.
4. **`PAPERCLIP_API_KEY` is not set** — step 1's fallback is defined above.
5. **The RPE1 arm is 24.2% partial with a non-random denominator** — if it is
   presented as independent replication, that is the second-most-likely attack.
6. **Scope creep into proteostasis writ large.** The gate passed the UPR/folding
   arm only; the broad proteasomal set failed. Claims must stay scoped.

---

# BUILD I + II OUTCOME — 2026-08-15

**Full record: `docs/BUILD_I_II_RESULTS.md`.**

> **The primary program (UPR) FAILED. The sealed held-out program (cholesterol)
> SUCCEEDED.** Opening line of the demo must pre-empt: *"our primary program
> failed, for a reason we can name — K562 has no ER stress, so the UPR was never
> engaged."*

| | UPR (primary) | Cholesterol (sealed, `9ad74a7`) |
|---|---|---|
| Top hit | MCM4 (replication licensing) | **SREBF2, rank 2/11,258, Tier 1** |
| Canonical regulators | not recovered (PERK/IRE1/XBP1 q≈0.8–1.0) | **both tails, correct sign** |
| q<0.05 | 517 | 773 |

**Framing settled:** two-tier output with an essentiality-matched null. Guide-pair
replication was recommended then killed by a 60-second check (738 genes = 7.5%
coverage). RPE1 is a generalisation check, never "the replication arm".

**The collision, quantified:** RPE1 covers **94.1%** of essential genes and
**11.3%** of non-essential ones.

**Divergence counts (113 UPR genes):** DISAGREES 90 / UNTESTED 12 / AGREES 11.

**Controls:** nonsense program 0 survivors (vs 517/773) ✅ · cholesterol
regulators recovered at both tails ✅ · UPR regulators not recovered ❌ ·
**guide-pair concordance −0.019** ❌ · top-50 essentiality 4.09× (p<0.001) ❌.

**scbench: ABANDONED, no number.** No `ANTHROPIC_API_KEY`, no Latch credentials,
not installed.

**Not done as specified:** Paperclip (unauthenticated — Europe PMC substituted);
Sanger KY cross-library agreement (only merged Chronos used).

---

# BUILD III — 2026-08-15

**Two-program story is the demo.** Full spine: `docs/DEMO.md`.

| | Program A (UPR) | Program B (cholesterol, sealed `9ad74a7`) |
|---|---|---|
| Result | **Correct null** | **SREBF2 rank 1 / 9,837** |
| Mechanism | K562 has no ER stress; the UPR was never engaged | 11/17 pathway members in extreme 10%, **p = 7.0e-08** |
| Sign correctness | — | **11/14 = 79%**, both tails |

**Seal predates the scoring code by 21 minutes** (seal 08:24:14, `score_k562.py`
created 08:45:15). Scripts byte-identical across both runs.

## Scope statement — on screen, verbatim, `docs/SCOPE_STATEMENT.md`

> Guide-pair concordance is −0.019. Independent guides targeting the same gene do
> not agree, so gene-level calls are not reproducible in this data. We make
> pathway-level claims only and name no novel gene. SREBF2 appears as a recovered
> known answer validating the ranking, not as a discovery.

Repo audited; **four violations found and fixed**, two planning docs annotated
SUPERSEDED IN PART.

## Evidence concentration — disclosed first

34 Paperclip sources for 113 genes · **0.30 sources/gene** · one review holds
**50.4%** (57 genes) · all 113 rest on exactly one source · only 14/113 top hits
name their own gene. Machine-readable in
`results/frozen/provenance.json → evidence_source_concentration`.
**It is a pointer layer, not an evidence chain. Do not call it one.**

## Frozen interface

`results/frozen/` — 5 files, fixed columns, `docs/DATA_DICTIONARY.md`.
Everything downstream reads these and never recomputes.

## Open risks

1. **−0.019 kills gene-level claims.** Pathway-level survives on the clustering
   statistic. **Pre-empt this in the opening sentence.**
2. **SREBF2 is a rediscovery.** Positive control, never a discovery.
3. **Evidence layer is concentrated** — reported by us, not found by a judge.
4. **Sanger KY never run.** Specified in Build II, not done.
5. **scbench abandoned** — no key, no Latch credentials. No number exists.
6. **Sign convention verified only internally** via SREBP tail-consistency.
   ~1 min to check properly; if inverted, the direction narrative flips.
7. **Two rank frames** (9,837 vs 11,258) already caused one error.
8. **Sponsor tools unauthenticated** except Paperclip. Modal + Benchling SDK
   installed (via `uv`; the venv has no pip). Proto/Biohub/Benchflow/Sundial have
   no discoverable public installer — credentials come at the lightning talks.
