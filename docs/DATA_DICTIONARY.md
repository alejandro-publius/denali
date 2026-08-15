# Data dictionary — `results/frozen/`

**Start here.** Written for someone with no biology background. Every file below
is frozen: the demo, the MCP server and the Streamlit page read these and
**never recompute anything**.

---

## What the experiment actually is, in four sentences

Someone took human cells and, one gene at a time, switched off ~9,800 different
genes. After each switch-off they measured which of ~8,200 other genes went up or
down. We define a **program** — a named list of genes that work together on one
job — and ask: *which switch-off pushes that whole program down hardest?*

We ran this twice. **Program A** is the unfolded protein response (cells coping
with badly-folded protein). **Program B** is cholesterol handling, and it was
**sealed in advance** — written down and committed to git before any scoring
code existed, so we could not tune anything to make it work.

---

## `program_a_scores.csv` and `program_b_scores.csv`

One row per gene that was switched off. 9,837 rows each. Same columns in both.

| Column | Plain English |
|---|---|
| `gene_symbol` | The gene that was switched off. |
| `rank` | 1 = switching this gene off pushed the program down hardest. 9,837 = pushed it **up** hardest. **Both ends are interesting** — the bottom of the list is genes that hold the program back. |
| `average_rank` | Position averaged across our three scoring methods, over 11,258 rows (some genes were tested more than once). This is what `rank` is sorted by. Lower = stronger. |
| `reversal_score_wilcoxon` | **The primary score.** How unusually the program's genes moved compared with every other gene, after this switch-off. Positive = program pushed **down**. Roughly: above +2 is notable, above +4 is strong. |
| `reversal_score_cosine` | A second, simpler score measuring the same thing a different way. Reported so no single number carries the claim. |
| `reversal_effect_size` | How *large* the average move was, as opposed to how *statistically unusual*. |
| `q_value` | Chance this is a fluke, adjusted for having tested ~11,000 genes. Below 0.05 is the usual bar. |
| `rpe1_rank` | Rank in a **second, different cell type**. Blank = **this gene was never tested there.** |
| `rpe1_covered` | `True`/`False`. **`False` means "we could not check", not "the check failed."** Never display a blank as if it were a clean result. |
| `depmap_gene_effect` | From an independent database: how badly cells are damaged by losing this gene. **More negative = more damaging.** Below −0.5 counts as essential. ⚠ **This is an average across ~1,178 different cell lines, not our cell line.** |
| `depmap_n_cell_lines` | How many cell lines that damage number is averaged over (~1,178). |
| `is_essential` | `True` if `depmap_gene_effect` < −0.5, i.e. cells struggle to live without it. Derived from the **mean**. |
| `tier` | Machine-readable confidence bucket (see below). **Derived from mean-Chronos.** |
| `tier_label` | The same thing as a sentence. **Use this on screen, not `tier`.** |
| `k562_chronos` | The same damage measure **in K562 specifically** (DepMap `ACH-000551`) — the actual cell line the experiment was run in. Blank for ~500 genes DepMap does not cover. |
| `tier_note` | **Empty for almost every row. Where non-empty, it OVERRIDES `tier_label`.** |

### ⚠ `tier` is mean-Chronos; `tier_note` overrides it where we checked

`tier` and `tier_label` come from the **1,178-line average**. We re-checked a
subset against **K562**, the line we actually scored in, and two genes disagreed.
We did **not** re-tier all 9,837 rows — we annotated only the rows we verified.

| Gene | mean | K562 | `tier` says | `tier_note` says |
|---|---:|---:|---|---|
| MBTPS2 | −0.492 | **−0.632** | not explained by fitness | `essential in K562 (Chronos -0.632)` |
| LDLR | −0.215 | **−0.568** | not explained by fitness | `essential in K562 (Chronos -0.568)` |

**UI rule: render `tier_note` wherever it is non-empty, in place of `tier_label`.**
Everywhere else, `tier_label` stands. An empty `tier_note` means "not re-checked
against K562", **not** "confirmed correct" — repo-wide, 555 of 9,333 genes (5.9%)
disagree between the two measures, and we have only annotated the two we verified.

### Tiers — why they exist

A gene can look like it "reverses" a program simply because switching it off is
killing the cell, and a dying cell's genes all move. Tiers separate those cases.

| Tier | Label | n |
|---|---|---:|
| `T1_reversal_not_explained_by_fitness` | Signal is not explained by the gene being essential | 7,857 |
| `T2_reversal_confounded_by_essentiality` | Gene is essential — signal may just be the cell dying | 1,541 |
| `T3_no_fitness_data` | No fitness data available for this gene | 439 |

**Tier 1 is the trustworthy bucket.** Our headline result, SREBF2, is Tier 1.

---

## `divergence_table.csv`

113 rows — one per gene in Program A's list. Asks: *the literature says this gene
matters; does our data agree?*

| Column | Plain English |
|---|---|
| `gene_symbol` | The gene. |
| `verdict` | `AGREES` / `DISAGREES` / `UNTESTED`. |
| `verdict_plain` | The same as a sentence. **Use this on screen.** |
| `reversal_score_wilcoxon`, `q_value`, `average_rank` | This gene's own switch-off result. |
| `paperclip_pmcid`, `paperclip_year`, `paperclip_title` | The paper Paperclip returned as evidence for this gene. ⚠ See the concentration warning below. |
| `epmc_pmid`, `epmc_year`, `epmc_title` | Europe PMC's top-cited matching paper. |
| `epmc_cited_by` | How many times **that paper** was cited. ⚠ **A property of the paper, not the gene.** |
| `epmc_paper_count` | How many papers mention this gene alongside the program. **This is the better measure of how well-studied a gene is.** |

**Counts: DISAGREES 90 · UNTESTED 12 · AGREES 11.**

`UNTESTED` means the gene is in the program but **was never switched off in the
experiment** — we have no opinion, not a negative one.

---

## `controls.csv`

Seven rows. A control is a check on whether the method works at all.

| Column | Plain English |
|---|---|
| `control` | Which check. |
| `program` | Which program it applies to. |
| `what_it_tests` | The question it answers. |
| `value`, `units`, `comparison` | The number and what to compare it against. |
| `verdict` | `PASS` / `FAIL` / `CAVEAT`. |
| `plain` | One sentence. **Use this on screen.** |

**Three of seven are FAIL and they are shown, not hidden.** A demo that shows
only passing controls is not evidence.

---

## `provenance.json`

The audit trail. Key fields:

| Field | What it proves |
|---|---|
| `seal.commit` / `seal.commit_time` | `9ad74a7`, **2026-08-15 08:24:14 −07:00** — when Program B was locked. |
| `commit_timeline` | Every commit with its timestamp. **The ordering is the whole argument.** |
| `pipeline_untouched_between_runs` | `true`. |
| `pipeline_evidence` | Both scripts byte-identical across the two runs, **and the seal predates the scoring code existing** (08:24:14 vs 08:45:15). |
| `preregistration_sha256` | `d7d90e41…` — thresholds hashed before any value was computed. |
| `data_checksums_sha256` | The exact input files. |
| `evidence_source_concentration` | See below. |
| `scope_limit` | The one-line limit on what may be claimed. |

---

## ⚠ Two warnings that must reach the screen

### 1. Gene-level calls are not reproducible

**Guide-pair concordance is −0.019.** Two independent tools aimed at the *same*
gene produce uncorrelated results. So: **pathway-level claims only, and no novel
gene is named anywhere.** SREBF2 appears as a *recovered known answer* validating
the ranking, not as a discovery. Full text: `docs/SCOPE_STATEMENT.md`.

### 2. The evidence layer is concentrated

| | Paperclip | Europe PMC |
|---|---:|---:|
| Genes with a source | 113 | 113 |
| Distinct sources | **34** | 75 |
| Sources per gene | **0.30** | 0.66 |
| Largest share held by one source | **50.4%** (57 genes) | 8.9% (10 genes) |
| Sources used for exactly one gene | 25 | 58 |
| Genes resting on exactly one source | **113 (all of them)** | 113 |

One review (`PMC12242609`) is the cited evidence for **57 of 113 genes**. Every
gene rests on exactly one source. **This is a real weakness and we report it
ourselves.**
