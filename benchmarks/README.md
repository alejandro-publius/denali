# denali as a benchmark

One BenchFlow task, built because their framing — *a benchmark is just a frozen
environment* — describes what this repository already was.

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
