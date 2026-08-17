# Leaderboard — does your method beat set size?

**Every number on this page is written by [`scorer/score.py --board`](scorer/score.py) and none is typed by hand.**
Regenerate with:

```
python benchmarks/challenge/scorer/score.py --board
```

Truth is the held-out RPE1 screen over 50 MSigDB Hallmark programs. `delta` is Spearman minus the size-only baseline's Spearman: **positive means the method beat set size.**

| # | method | Spearman | top-10 | delta vs baseline |
|--:|---|--:|--:|--:|
| 1 | raw K562 hit count | 0.6633 | 0.80 | +0.2082 |
| 2 | hits per gene measured | 0.6599 | 0.70 | +0.2048 |
| 3 | denali rerank residual | 0.4664 | 0.40 | +0.0113 |
| 4 | **size only (baseline)** | 0.4551 | 0.60 | +0.0000 |

The size-only baseline scores rho **0.4551** against a permutation null whose 95th percentile of |rho| is 0.2781 (p = 0.0014), so it is a baseline worth beating rather than a straw man.

## How to enter

Open a pull request adding one CSV to [`entries/`](entries/). No server, no account, no hosting — the pull request **is** the submission mechanism, and the scorer reruns every entry in `entries/` on every run, so a row that cannot be reproduced from its own file does not survive.

## The row that matters

**`denali rerank residual` is this project's own method, entered as a contestant.**
Where it lands is where it lands. A benchmark authored by the party it flatters is marketing, so it is scored by the same code as everyone else and its result is printed in the same type size.

## What a high row is not

Ranking well here means predicting the second screen, and predicting the second screen is not the same as being right. Both screens can be confounded the same way and agree for the same wrong reason — that is this project's own evaluation 6, which found 26% of the cross-screen agreement is set size rather than biology. No row on this board is an endorsement of any gene set, and no gene is named.
