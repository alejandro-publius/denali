# Evaluation 8 — off-target nomination as a construction statistic

**POST-HOC. NOT PRE-REGISTERED. Thresholds SWEPT, not chosen.** Same labelling as
evaluation 6, for the same reason: this arm was built after the freeze, so no
single threshold in it is entitled to be called the deciding one. Every hit rule
we could defend is reported and the spread is the result.

Neither dataset is ours. Both are published supplementary tables.

## Getting the data

`data/offtarget/` is git-ignored — 20 MB of published workbooks that anyone can
re-fetch. Both are stable Springer ESM URLs.

```bash
mkdir -p data/offtarget
curl -sSL -o data/offtarget/changeseq.xlsx \
  "https://static-content.springer.com/esm/art%3A10.1038%2Fs41587-020-0555-7/MediaObjects/41587_2020_555_MOESM3_ESM.xlsx"
curl -sSL -o data/offtarget/crisprme.xlsx \
  "https://static-content.springer.com/esm/art%3A10.1038%2Fs41588-022-01257-y/MediaObjects/41588_2022_1257_MOESM4_ESM.xlsx"
.venv/bin/python -m src.offtarget_audit
```

sha256, so a silently re-versioned supplement is detectable:

| file | sha256 |
|---|---|
| `changeseq.xlsx` | `f4a48a985b8616d4fa29798da153da65672170a434f1d4d845fd9163d0ee91fa` |
| `crisprme.xlsx` | `aa34a0dd6d18acf16a3555e5d821c556dadf2b6db62a41c117d60345769c0344` |

The script is deterministic: two consecutive runs produce a byte-identical
`offtarget_evaluation.json`. No auth, no network, no model weights.

## Arm 1 — CHANGE-seq vs GUIDE-seq

Lazzarotto et al., *Nat Biotechnol* 2020, doi:10.1038/s41587-020-0555-7,
Supplementary Tables 3 and 6. 202,043 biochemically nominated sites over 110
guides; ST6 is GUIDE-seq — a **cellular** assay — on 56 of the same guides. Two
assays, same guides, different physical principle.

The confound is the one this project keeps finding, wearing different clothes. In
our own data a gene set's **size** inflated its hit count. Here a guide's **search
yield** — how many candidate sites the mismatch budget nominated — does the same
job. A guide whose search returns thousands of sites has more chances to be
confirmed than one returning hundreds, and that is arithmetic, not guide biology.

**85.2%** of the 202,043 nominated sites sit at 5 or 6 mismatches: the permissive
tail the mismatch budget creates.

Across seven read-count thresholds, the share of biochemical–cellular agreement
explained by search yield runs **17.6% – 33.9%, median 31.2%**. R² of search yield
against cellular hit count: **0.36 – 0.55**.

Compare our own cross-screen concordance arm: **26%**. Same direction, modestly
stronger. Not dramatically so, and we do not say dramatically.

### A tautology this arm refused to report

Regressing search yield on the **biochemical** hit count instead gives R²
**0.83 – 1.00**, and exactly **1.0000** at the two lowest thresholds. That is not a
finding. Every nominated site has at least one read, so at those rules the hit
count *is* the yield and the regression is an identity. The reported R² is the
cellular direction, the only one that can carry information. The tautological
figure is kept in the output JSON because it is the number this arm would have
overstated itself with, and burying it would be the more comfortable choice.

## Arm 2 — CRISPRme

Cancellieri et al., *Nat Genet* 2022, doi:10.1038/s41588-022-01257-y,
Supplementary Data 2. Top 1,000 sites by CFD for each of 14 therapeutic guides.

**Not a discovery.** That genetic variants create off-target sites is the finding
of the CRISPRme paper itself. Recovering it confirms the pipeline reads the data
correctly and is not presented as new.

**What this adds** is the per-guide fraction as a construction statistic — and a
separation between two quantities that are easy to conflate:

| quantity | column | n / 14,000 | share | per guide |
|---|---|--:|--:|---|
| best alignment comes from an **alt allele** | `REF/ALT_origin` | 6,179 | **44.1%** | 40.1% – 52.1% |
| site is **absent from the reference** | `Not_found_in_REF` | 1,737 | **12.4%** | 8.5% – 20.2% |

PAM-creating variants: **23 – 65** per guide.

These are not the same statement. The first says a variant makes the site a
*better* match; the site may still exist in the reference. The second says the
site is not in the reference at all. Quoting 44.1% while describing it as "exists
only on a non-reference allele" overstates the effect roughly threefold. We hit
exactly that error while building this arm and it is recorded here rather than
quietly corrected.

**The denominator is not the genome.** It is the top 1,000 by CFD per guide — a
ranked selection, already sorted by predicted activity. Every percentage above is
a share of that shortlist.

## Scope

No guide is named safe or unsafe, and none is ranked. These are properties of how
off-target lists are **constructed**, not verdicts on any guide. A tool that
turned a confound estimate into a clinical recommendation would be committing the
error it exists to detect — the same rule that stops `src/audit_screen.py`
nominating a gene set, applied to a domain with a patient at the end of it.

This arm does not revise the pre-registered K562 primary in `results/frozen/`.
