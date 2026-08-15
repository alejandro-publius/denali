# Data dictionary — `results/frozen/`

**Start here.** Written for someone with no biology background. Every file is
frozen: the demo, the MCP server and the Streamlit page read these and **never
recompute anything**.

---

## What the experiment is, in five sentences

Someone took human leukemia cells (called K562) and, one gene at a time, switched
off ~9,800 different genes. After each switch-off they measured which of ~8,200
other genes went up or down. A **program** is a named list of genes that work
together on one job — "handle cholesterol", "cope with damaged protein". For each
program we ask: *which switch-off pushes that whole program the other way?*

We did this for **all 50 programs in a standard public collection** (MSigDB
Hallmark), so we could not cherry-pick which ones to show you.

---

## `matrix.csv` — the main result

**Rows = 9,837 genes that were switched off. Columns = 50 programs.**
Each cell is one number: how strongly switching off that gene moved that program.

- **Positive** = switching the gene off pushed the program **down**
- **Negative** = pushed it **up**
- Roughly: above +2 is notable, above +4 is strong
- Blank = that gene wasn't measurable for that program

---

## `program_summary.csv` — one row per program

| Column | Plain English |
|---|---|
| `program` | The program's name. |
| `rank_by_R_p` | 1 = most "reversible" program of the 50. |
| `n_declared` | Genes the program is defined to contain. |
| `n_present` | How many of those we could actually measure. |
| `frac_present` | `n_present` ÷ `n_declared`. |
| `n_hits_q05` | **How many of the 9,837 switch-offs measurably moved this program.** |
| `R_p` | `n_hits_q05` on a log scale, so big and small programs are comparable. |
| `reversibility_call` | `reversible` / `weak` / `null`. |
| `call_plain` | Same thing as a sentence. **Use this on screen.** |
| `expr_ratio` | How highly the program's genes are expressed vs. everything else. Above 1 = higher. |
| `sd_ratio` | How much they move around vs. everything else. Above 1 = more. |
| `essentiality_density` | Fraction of members the cell can't live without. |
| `coherence` | How much the members move together. ⚠ Computed from the same data as `R_p` — see the circularity note in `provenance.json`. |
| `passes_measurability_gate` | Did the program clear our pre-set bar for being measurable at all. |
| `measurability_limited` | `True` = the program's result may say more about our ability to measure it than about its biology. |
| `R_p_predicted_from_measurability` | What a model using **only** the six measurability features predicts. The column name is historical and frozen: a post-freeze split showed the variance is carried by set *construction* (chiefly size, adj R² 0.697), not measurement quality (0.152). See `LIMITATIONS.md` §0. |
| `R_p_residual_after_measurability` | Observed minus predicted. **This is the part that might be biology.** Near zero = fully explained by measurement. |
| `is_sealed_program_B` | `True` for the one program locked in git before the analysis existed. |
| `is_program_A` | `True` for the program we chose first, which returned a null. |

---

## `heldout.csv` — the held-out set

Ten programs from a **different** collection, chosen by a public rule (no human
picked them). They were not looked at until the prediction model was finished and locked, then scored once. This is how
we test whether the model works on things it has never seen.

---

## `provenance.json` — the audit trail

| Field | What it proves |
|---|---|
| `preregistration.sha256` | The rules were hashed and committed **before** the sweep ran. |

| `seal.seal_intact` | `true` = the scoring code is byte-identical to the version that produced these numbers. A methods check, not a claim. |
| `deciding_statistic` | The pre-set test and which conclusion it triggered. |
| `gap_numbers` | The headline counts. |
| `evidence_layer` | How badly our literature tool performed when we audited it. |

---

## ⚠ Three warnings that must reach the screen

**1. Gene-level calls are not reproducible.** Two independent tools aimed at the
same gene give uncorrelated results (**−0.019**). **Pathway-level claims only. No
novel gene is named anywhere.**

**2. `measurability_limited` is not a footnote.** A model using only measurement
quality explains **75%** of which programs look reversible. Most of what looks
like biology here is an artifact of how the gene sets were built — chiefly their size.

**3. Blank ≠ negative.** A blank cell or an unscored program means *we could not
check*, never *we checked and it was fine*.
