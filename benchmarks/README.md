# denali as a benchmark

Two BenchFlow tasks, built because their framing — *a benchmark is just a frozen
environment* — describes what this repository already was.

Each turns one of this project's findings into a test of somebody else. Neither
grades us: no denali result depends on either, and the answer keys live with the
verifiers, outside the containers.

## `tasks/denali-gate-trap`

Our second finding was that the obvious quality filter is wrong 20 times out of
50: programs that fail a measurability gate return real results anyway. This task
turns that into a test of somebody else.

An agent is given **only** measurability features for 50 gene programs — how many
declared genes were detected, expression ratio, variability, essentiality — and
must predict which of them returned at least one significant hit in a
genome-scale CRISPRi screen. It never sees the screen's results; the answer key
lives with the verifier, outside the container.

| Strategy | Balanced accuracy | Reward |
|---|--:|--:|
| Always "yes" | 0.5000 | 0.0000 |
| **The naive measurability gate** | **0.6981** | 0.3963 |
| Reference solution (`oracle/solve.sh`) | 0.7413 | 0.4825 |
| Perfect | 1.0000 | 1.0000 |

The naive gate fails with **20 false negatives and 1 false positive** — it is not
noisy, it is biased in one direction. Beating it means noticing that measurability
predicts how *much* signal a program shows, not *whether* it shows any.

## Validated

```
bench tasks check tasks/denali-gate-trap     # valid (structural)
docker build ./environment                   # builds
oracle -> verifier                           # 0.7413, beats the gate
```

The verifier discriminates rather than rubber-stamping: a missing answer scores
0.0, malformed JSON scores 0.0, an incomplete answer scores 0.0, and answering
everything "true" scores 0.0. Reproducing the naive gate inside the container
returns 0.6981 — exactly the figure measured independently in the main pipeline,
which is a check on the answer key as much as on the task.

**This grades other people's agents, not ours.** No denali result depends on it.

## `tasks/denali-confound-estimate`

Our *first* finding, turned into a test. An agent gets seven `set,size,hits`
tables from seven **real published studies** — CRISPR-KO, CRISPRi, CRISPRa,
single-cell, organoid, primary human T cell, bulk RNA-seq — and must estimate,
for each, what fraction of the ranking is explained by set size alone.

The measured answers span **0.36 to 0.88**, and every one of those studies was
published. That spread is the task: guessing "they're all confounded, call it
0.6" gets the direction right and the magnitude wrong on all seven.

| Strategy | MAE | Reward |
|---|--:|--:|
| Constant 0.5 | 0.1585 | 0.0000 |
| **Constant at the true mean (0.5962)** | **0.1395** | **0.0000** |
| Reference solution (`oracle/solve.sh`) | **0.0000** | **1.0000** |

Reward normalises against the **stronger** baseline — the constant that already
knows the right average and still cannot tell the screens apart. Normalising
against the weaker one would have paid out for guessing the mean, which is the
behaviour the task exists to catch.

There is a trap in the data and it is not decorative: the seven screens carry
between **17 and 2,809 sets, and the smallest is the most confounded**. Any
approach assuming more data means more confounding has the sign backwards.

### The oracle was wrong the first time

Worth recording, because it is the same error class this project keeps finding.
The first reference solution regressed `log10(1 + hits)` on **`log10(size)`** —
symmetric, tidier, and wrong. It scored **MAE 0.1474 against the key, worse than
a constant**, which would have shipped a task whose own oracle failed it.

The auditor regresses on **raw** size. The confound is that a set with twice the
genes gets roughly twice the chances, and that is linear in size; compressing
that axis measures a weaker, different thing. Corrected, the oracle reproduces
all seven values exactly (MAE 0.000000).

## Validated

```
bench tasks check tasks/denali-gate-trap          # valid (structural)
bench tasks check tasks/denali-confound-estimate  # valid (structural)
oracle -> verifier                                # 0.7413 / 1.0000
```

Checked against **benchflow 0.6.9**. Two findings from that revalidation:

- **`denali-gate-trap` no longer parsed.** 0.6.9 renamed the `environment:` key
  to `sandbox:`, so the task that this README called "valid (structural)" had
  silently stopped being valid against the current release. Renamed and
  revalidated. A benchmark that does not load is worth less than no benchmark,
  and nothing here would have caught it without running the check again.
- The `environment/` **directory** name is unchanged; only the `task.md` key moved.

Both verifiers discriminate rather than rubber-stamping. For
`denali-confound-estimate`, measured across ten adversarial cases:

| Answer | Reward |
|---|--:|
| Oracle, exact | **1.0000** |
| Constant 0.5 · constant true mean · all zeros · all ones | 0.0000 |
| One screen missing · value outside [0,1] · string instead of number | 0.0 |
| Malformed JSON · no answer file at all | 0.0 |
