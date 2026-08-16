# Corrections arm (Track B) — pre-registration

**Written and committed before the ORCS substrate was downloaded and before any
correction was computed.** No threshold below was chosen after seeing a value.

**Post-deadline extension work.** The eleven closed evaluations are not revised.
`results/frozen/` and `results/corpus/` are not touched; outputs go to
`results/corrections/` on a branch.

---

## The question, scoped honestly

The literature has proposed fixes for the size confound for fifteen years:
CAMERA's variance-inflation factor (Wu & Smyth 2012, doi:10.1093/nar/gks461),
size-preserving permutation nulls, and the ordinary hypergeometric ORA that
most tools actually ship. denali cites CAMERA as the theory it recovered
empirically — but nobody has measured, across a large corpus of real screens,
**how much of the size dependence each correction actually removes**, or how
often a correction makes it worse.

The strongest standing objection to the corpus headline is: *"nobody ranks
sets by raw hit counts; everyone uses a hypergeometric p-value, which already
conditions on set size."* This arm measures whether that is true as a matter
of arithmetic on 1,272 real screens.

## Substrate, fixed before download

BioGRID ORCS human screens tarball (`docs/CORPUS.md` gives the download and its
HTTP/1.1 gotcha; expected 752,653,348 bytes for 2.0.18 — if BioGRID has since
released a newer version, the version actually downloaded is recorded and the
overlap check below applies to matching screen IDs only). Gene sets: MSigDB
Hallmark v2026.1.Hs, the committed GMT. **Inclusion rule verbatim from
`src/corpus_audit.py`:** ≥ 20 hits, ≥ 10,000 genes measured, ≥ 8 usable sets
(a set is usable with ≥ 5 measured members).

**Pipeline validation gate, before any correction number is read:** recompute
`r2_size_alone` (log-size predictor, the corpus transform) per screen and
compare to the committed `results/corpus/corpus_per_screen.csv`. If fewer than
99% of matching screen IDs agree within ±0.0005, STOP and reconcile; no
correction result is reported from an unreconciled pipeline.

## The corrections, fixed now

Per screen, per Hallmark set with m measured members and k member-hits, in a
screen measuring M genes with H total hits:

| ID | Correction | Statistic ranked |
|---|---|---|
| C0 | none (baseline, what denali audited) | k (equivalently log10(1+k)) |
| C1 | ORA hypergeometric, the field's actual default | −log10 upper-tail p of Hypergeom(M, H, m) at k |
| C2 | size-preserving permutation null, standardized | z = (k − E[k]) / sd[k] under the same hypergeometric. For binary hit data a permutation that preserves set size and draws from measured genes IS the hypergeometric; this is computed analytically and the identity is stated, not hidden |
| C3 | competitive score test (CAMERA at ρ̄=0; also what MAGMA's competitive regression reduces to absent per-gene covariates) | \|z\| where z = (mean in-set SCORE.1 − mean out-set) / (sd_all · √(1/m + 1/(M−m))). Only on screens where SCORE.1 parses finite-numeric for ≥ 80% of measured genes |
| C4 | CAMERA VIF-inflated competitive test | as C3 with the denominator's 1/m term inflated by VIF = 1 + (m−1)ρ̄, at ρ̄ = 0.01 and ρ̄ = 0.05 (fixed; the typical values discussed by Wu & Smyth). Inter-gene correlations are not computable from ORCS hit tables and this is stated as the arm's main limitation, not discovered later |
| C5 | denali's own residualisation (`core.rerank` verbatim) | residual of log10(1+k) on m |

**Declared not-applicable now, so it is not decided after the fact:**
GOseq corrects a per-gene covariate (transcript length), not set size — no
analogous per-gene covariate is in scope. SetRank corrects inter-set overlap,
not size; a faithful implementation is out of scope. Both are reported as N/A
with these reasons, not as failures.

## Metrics, fixed now

Per screen × correction:

- **Primary:** ρ²_s = squared Spearman correlation between the ranked
  statistic and set size m. Rank-based because the corrections emit statistics
  on incomparable scales, and because it does not hand C5 a win by
  construction (linear residualisation zeroes the linear R² identically but
  not the rank correlation).
- before = ρ²_s of C0; after = ρ²_s of the correction.
- **Relative reduction** = 1 − after/before, aggregated only over screens with
  before ≥ 0.05 (floor fixed now; below it the ratio is noise).
- **Worse rule:** a correction made a screen worse if after > before + 0.05.
- **Secondary:** the linear-R² versions (continuity with the published
  headline); top-10-by-C0 vs top-10-by-correction overlap, descriptive.

## Verdicts per correction, fixed now

| Outcome | Threshold |
|---|---|
| WORKS | median relative reduction ≥ 0.50 AND worse-share ≤ 5% |
| PARTIAL | median relative reduction in [0.20, 0.50) and worse-share ≤ 15% |
| FAILS | median relative reduction < 0.20 OR worse-share > 15% |
| WORKS ON MEDIAN, UNRELIABLE TAIL | median ≥ 0.50 AND worse-share > 5% |

**Pre-registered obligation:** if C5 (denali's own correction) has a median
relative reduction lower than any of C1–C4 by more than 0.05, the report MUST
state that the tool should recommend that method rather than itself, in the
same sentence that reports C5's number.

**Pre-registered caveat:** driving ρ²_s to zero proves size-decoupling, not
correctness — a correction that deleted all biology would also score
perfectly here. No correction is declared "right", only measured for how much
size dependence survives it. Ground truth does not exist in this corpus and
we will not pretend otherwise.

## What would make us report neither

- Fewer than **800** screens pass inclusion (1,272 expected): investigate
  parsing before proceeding. Fewer than **400**: no verdict, arm reported
  UNDERPOWERED.
- The validation gate above fails and cannot be reconciled: no verdict.
- C3/C4 are additionally reported on their own sub-corpus (screens with usable
  SCORE.1); if that sub-corpus is < 200 screens, C3/C4 get no verdict and the
  count is reported.

## Constraints

1. No screen, publication, or gene set is named as a finding. The unit of
   inference is the distribution.
2. The screen is not the independent unit (`docs/CORPUS.md`): every headline
   distribution is also reported publication-collapsed (median per source_id),
   and neither number is quoted alone.
3. `results/frozen/` and `results/corpus/` untouched.
