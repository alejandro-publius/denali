# Handoff — resume with zero explanation

**Repo:** https://github.com/alejandro-publius/reversal-map (private)
**Read order:** this file → `REPORT.md` → `docs/DEMO.md`. Nothing else needed.

**ANALYSIS IS CLOSED.** No new sweeps, no refits, no new features, no gene-level
claims. Remaining work is communication and hardening only.

---

## 1. What this is, in three sentences

We scored all 50 MSigDB Hallmark gene programs against 9,837 CRISPRi knockdowns
in K562 and asked which programs are "reversible" — i.e. which have many
knockdowns that move them. **Most of the answer turns out to be measurement, not
biology.** Four evaluations were run, three came back negative, and all four are
reported.

## 2. The four results

| | Result | Verdict |
|---|---|---|
| **NEG 1** | Measurability explains **56–75%** of variance in apparent reversibility (adj R² 0.561 X-independent / 0.751 all-six). Pre-registered claim **(b)** fired against a 0.60 threshold fixed before the sweep. Program size alone = 46.5%. | Reported as the finding |
| **NEG 2** | The measurability gate is **wrong 20 of 50**. Only 1/50 passes with zero hits. The **sealed** program fails the gate (`expr_ratio` 0.92) and ranks **11/50 with 773 hits**. | Our own filter would have discarded our best result |
| **NEG 3** | Held-out: **UNDERPOWERED AND INCONCLUSIVE** (1/10 passed the gate; rule fired below 8/10 before any number was seen). Axis 1 ρ = +0.526, CI **[−0.101, +0.913]** → PARTIAL. Axis 2 balanced accuracy **0.4375**, zero true positives → **FAILURE**. | Not refit |
| **POS** | Sealed SREBF2 recovery, rank 2 of 11,258 scored perturbations (larger than 9,837 unique genes; some are targeted twice). 11 of 17 canonical members in the extreme 10%, p = 7.0×10⁻⁸, 79% sign-correct both tails. | A **control**, not the headline |

Also: **essentiality density is flat at program level**, +0.021, p = 0.90.

Clearest single illustration: `REACTOME_SCAVENGING_OF_HEME_FROM_PLASMA` drew the
**highest** held-out prediction (R_p 5.26), has **one** measured member, returned
**zero** hits. The failure and the finding are the same fact.

## 3. Hashes and seals — the provenance spine

| Artifact | Value |
|---|---|
| Matrix pre-registration | **`d3e24b77…`** (supersedes `7d28436d…`), commit `c4d5d91` |
| Gate C1 pre-registration | `d7d90e41…`, commit `280c626` |
| **Frozen predictor** | **`610f2a75…`**, commit `d902803` — frozen *before* the held-out set was opened |
| **Held-out program seal** | **`9ad74a7`, 08:24:14** |
| Scorer, byte-identical condition | `2abfdc6f…` |

⚠ **The 21-minute gap is the core claim:** the seal landed at 08:24:14;
`src/score_k562.py` was created at **08:45:15**. The held-out program was fixed
*before the scoring code existed*.

⚠ **Byte-identical scorer condition:** any sweep must call `src/score_k562.py` at
sha256 `2abfdc6f…`. **If that hash changes, the seal at `9ad74a7` is void** and it
must be said out loud, not quietly kept. Verified in `provenance.json` as
`seal.seal_intact`.

## 4. ⚠ Partial-visibility disclosure — know this before a judge asks

During the held-out run the script crashed twice (undefined `coherence` at <2
measured members; BH correction on zero scoreable perturbations). **Three of ten
rows had already printed** when the first guard was written, so part of the
held-out set was visible at that moment.

Prepared answer is in `docs/DEMO.md`. **Lead with point 1:**

1. **The result was a FAILURE** — contamination biases toward looking good, not
   toward worse-than-chance with zero true positives.
2. The frozen predictor `610f2a75` was never touched; only feature extraction was.
3. Guards are neutral by construction (training-mean imputation → z = 0).
4. The inconclusive verdict fired on a pre-registered rule before any number was
   visible.

In `docs/LIMITATIONS.md` §7 because we wrote it down, not because someone found it.

## 5. DONE

- Tier 1 sweep, 50 programs × 9,837 knockdowns, 9.2 min, local
- Frozen interface: `matrix.csv`, `program_summary.csv`, `heldout.csv`,
  `predictor.json`, `provenance.json`, `controls.csv`,
  `divergence_by_program.csv`, `program_a/b_scores.csv`
- `docs/DATA_DICTIONARY.md`, plain English, no biology assumed
- Tier 3 predictor frozen and hashed; Tier 2 held-out scored against it
- `src/next_experiment.py` — three branches, generated not hardcoded
- Four figures + `results/figures/CAPTIONS.md` (identical wording everywhere)
- `REPORT.md`, `docs/LIMITATIONS.md`, `README.md` (six sentences)
- `docs/DEMO.md` rebuilt on the 3:1 structure, 2:57, adversarial Q&A ranked
- `src/mcp_server.py` — one tool: measured / predicted / unscored + next experiment
- Tools working: Claude Code, Paperclip, Modal, ESMC (real forward pass), Benchflow

## 6. ABANDONED — say so plainly if asked, claim nothing

| | Why |
|---|---|
| **scbench** | No `ANTHROPIC_API_KEY`, no Latch credentials. **No score exists; claim none.** |
| **Sanger KY cross-library** | Specified in Build II, never run |
| **Benchling** | Free personal account has no Developer Platform. Account-tier blocker, not a login problem. **Nothing to register — skipped.** |
| **Sundial** | No discoverable install path. The PyPI `sundial` is an unrelated hobbyist library and was deliberately **not** installed to inflate the count |
| **Modal for Tier 1** | 8 min locally vs ~40 min plumbing. Would have been decoration |
| **Tier 4 / C2 CP** | Lands after the hard freeze; cannot enter `results/frozen/` |

## 7. NOT STARTED

- Streamlit page (Rachel owns it; builds against `results/frozen/`)
- MCP server registered with a client — code exists and is tested, not wired
- Clean-clone reproduction check — **Sunday 10:00, 20 min budget**
- Any phenotypic validation. Transcriptional movement is not phenotypic reversal

## 8. Reproduce

```bash
cd ~/figure-contract
.venv/bin/python -m src.sweep             # 9.2 min, 50 x 9,837
.venv/bin/python -m src.freeze_matrix
.venv/bin/python -m src.freeze_predictor  # hash MUST be 610f2a75...
.venv/bin/python -m src.score_heldout
.venv/bin/python -m src.figures_matrix
```

Landmines: the venv has **no pip** (built with `uv`) · `modal` lives at
`.venv/bin/modal`, not on PATH · figshare 403s on HEAD but 206 on ranged GET ·
`urllib` SSL is intercepted, use `curl` · Replogle `X` is a perturbation-**effect**
matrix, not expression; absolute expression is `var/mean` · non-finite entries
exist — **mask, never impute**.

## 9. Standing rules

Pathway-level claims only · **no novel gene named anywhere** · no refits · never
revise a pre-registration · no agents or subagents · figures from our own data
only, since a protein render would imply a gene-level claim · **no claims about
how fast this was built**.

## 10. For Rachel

Start at `docs/DATA_DICTIONARY.md`, then `docs/SCOPE_STATEMENT.md`. Build the
Streamlit page against **`results/frozen/`** only — never recompute. Four rules
the page must not break:

1. **Name no novel gene.** SREBF2 appears only as a recovered known answer.
2. **`rpe1_covered = False` renders as "NOT CHECKED"**, never a blank or a pass.
3. **Any ranked list carries −0.019 on screen.**
4. **Show the failing controls.** Three of seven are FAIL and that is the point.

⚠ Two rank frames exist: `rank` is over 9,837 unique genes, `average_rank` over
11,258 perturbation rows. Pick one and never mix them — this already caused one
error.
