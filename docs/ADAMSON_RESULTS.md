# Adamson 2016 arm — result

**Pre-registered** at [`docs/ADAMSON_PREREG.md`](ADAMSON_PREREG.md), sha256
`4a7ece03…`, committed `7a98d4d` — **before this analysis code existed and before
the substrate was opened**. Amended at `9b96318` (sha256 `b83e7308…`) to resolve a
substrate ambiguity; **no threshold was changed** and the original text is
untouched and diffable.

## What was run, stated exactly

> **The frozen scorer, unmodified, plus a pre-registered construction step we
> wrote.**

That phrasing is deliberate and it is the honest one. This is **not** "an
unmodified rerun." Two separable things happened:

1. `score()` from `src/score_k562.py` (sha256 `2abfdc6f…`) was **imported and
   called unmodified**. The file was not edited; the arm asserts its hash at
   startup and abandons if it moved.
2. The frozen scorer eats a **perturbation-effect matrix**. Adamson ships
   **sparse single-cell counts**, so an effect matrix had to be built. **That
   construction is new code we wrote.** It is *not* covered by the scorer's hash,
   it is a genuine degree of freedom, and it was fixed in the pre-registration
   before the substrate was opened. `adamson_evaluation.json` records
   `substrate_construction_covered_by_scorer_hash: false`.

Anyone describing this arm as the identical pipeline re-run on new data is
describing something that did not happen.

## Scope — not a replication

Adamson is a **targeted UPR library**: 103 perturbations after the pre-registered
25-cell floor, against K562's 9,837 genome-scale knockdowns. Two orders of
magnitude smaller and deliberately enriched for regulators of the very program
under test. It is the worst substrate for a claim about unbiased screens and the
best available one for a claim about engagement, and it is used only for the
second.

## The premise was checked first, and it held

denali's own recorded design failure is that K562 is unstressed, so the UPR was
never switched on — the gate tested whether a program was *measurable* when it
should have tested whether it was *engaged*. This arm exists to answer that, so
the premise had to be established rather than assumed.

**P0 — ESTABLISHED.** Mean absolute perturbation effect across the 101 measured
UPR genes: **0.0551**, against a null of 1,000 gene sets matched on **both size
and control-expression decile**: 99th percentile **0.0487**, empirical
**p = 0.001** (the floor of the 1,000-draw null). Decile matching was in the
pre-registration, not added afterwards — UPR genes are more highly expressed, and
an unmatched null would have declared engagement for that reason alone.

The program is engaged. The objection can now be answered with data.

## Result — claim (a) supported

| Gate | Pre-registered rule | Observed | |
|---|---|--:|---|
| P0 engagement | above 99th pct of matched null | p = 0.001 | **passed** |
| P1 scoreable | ≥ 35 of 50 | **50 / 50** | **passed** |
| P2 programs with ≥1 hit | ≥ 15 of 50 | **39 / 50** | **passed** |
| **Deciding statistic** | `R²` ≥ 0.25 **and** slope > 0 | **R² 0.2685**, slope **+0.00719**, p = 1.16×10⁻⁴ | **claim (a)** |

**VERDICT: PERSISTS UNDER ENGAGEMENT.** The size confound is not an artifact of
having scored dormant programs. It is structural.

For context, not as a threshold: K562 **0.4649**, RPE1 **0.2758**, Adamson
**0.2685**.

## The margin is thin, and one control definition falls below the bar

The same disclosure the RPE1 arm made, and it applies harder here. **The bar was
0.25 and the result is 0.2685 — it clears by 0.0185.** The pre-registered
sensitivity on the control definition is the reason to be careful:

| Control definition | Cells | `R²` | Slope | Would have been |
|---|--:|--:|--:|---|
| **Pooled (primary)** | 7,293 | **0.2685** | +0.00719 | claim (a) |
| `Gal4-4(mod)_pBA582` alone | 1,283 | 0.2699 | +0.00699 | claim (a) |
| `63(mod)_pBA580` alone | 6,010 | **0.2398** | +0.00701 | **INCONCLUSIVE** |

**Two of three control definitions clear 0.25 and one does not.** That is
reported because it is true, not because it was asked for. The pooled definition
was fixed in the amendment on power grounds *before* any of these three numbers
existed, so the primary is not a choice among answers — but a reader is entitled
to know the verdict sits close enough to the bar that a defensible alternative
control lands in the inconclusive band.

**What is stable is the effect, not the threshold crossing.** The slope is
essentially identical across all three definitions (**+0.00699 to +0.00719**,
p ≤ 3.1×10⁻⁴ in every case). The size relationship is robust and positive
whichever control is used; it is the *variance explained* that wobbles across an
arbitrary line. The honest summary is that the size effect reproduces under
engagement with a consistent slope, and that the pre-registered `R²` bar is
cleared narrowly rather than comfortably.

## Secondary, descriptive, no threshold

Spearman ρ between K562 and Adamson `R_p` across all 50 programs: **+0.7218**
(p = 3.3×10⁻⁹, n = 50). Descriptive only — no threshold was set for this and none
is applied after the fact. The library designs differ by two orders of magnitude
in size and by intent, so this number should not be read as replication.

## Construction, as recorded in the artifact

65,337 cells × 32,738 genes → **11,987 genes** retained at 1% detection; cells
normalised to 10,000 counts and `log1p`'d; **103 perturbations** retained at the
25-cell floor (10 dropped); control = every construct carrying `(mod)` on a `pBA`
vector, **pooled**, = `63(mod)_pBA580` (6,010) + `Gal4-4(mod)_pBA582` (1,283) =
**7,293 cells**. `62(mod)_pBA581` carries 2 cells and was excluded by the
**original** 25-cell floor, not by anything introduced after the fact.

## Constraints honoured

- `results/frozen/` untouched. This arm writes `results/adamson/` only.
- The K562 pre-registered primary is **not** revised by this arm.
- **No gene-level claim.** Guide-pair concordance forbids it here as in K562, and
  no novel gene is named.
- Computational only. Transcriptional movement is not phenotypic reversal; no
  wet-lab, dosing, clinical or therapeutic claim follows.

> **Commit references, after integration.** This arm was rebased onto `main`
> when it merged, which rewrote its commit hashes. `7a98d4d` → **`555ea5c`**
> (pre-registration) and `9b96318` → **`fe4afa9`** (amendment). The original
> hashes appear above and in `adamson_evaluation.json` because that is what
> was true when the arm ran, and rewriting a result artifact to match a later
> rebase would be the opposite of what this document is for. The content is
> unchanged and is verified by sha256, not by commit: the text above the
> amendment line still hashes to `4a7ece03…`, and a test asserts it.
