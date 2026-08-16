---
schema_version: "1.3"
metadata:
  author_name: "denali"
  difficulty: hard
  category: capability
  tags: ["genomics", "crispr", "confound-detection", "gene-set-enrichment", "metascience"]
agent:
  timeout_sec: 1200
verifier:
  timeout_sec: 120
sandbox:
  cpus: 1
  memory_mb: 2048
---
# denali-confound-estimate

## prompt

`data/` holds seven gene-set enrichment results from seven **real, published**
studies. They are different assays in different labs — CRISPR knockout, CRISPRi,
CRISPRa, single-cell, organoid, primary human T cell, and bulk RNA-seq — and each
file is the table such an analysis already produces:

```
set,size,hits
cellular macromolecule biosynthetic process (GO:0034645),314,42
glycolytic process (GO:0006096),29,14
```

`size` is how many genes were measured in that set. `hits` is how many came back
significant. Nothing else about the biology is available to you, and you do not
need it.

**Task.** For each screen, estimate what fraction of the variance in that
ranking is explained by **set size alone** — that is, how much of the ranking
you could reproduce knowing only how big each set is, with no reference to what
any gene does.

Write `/logs/artifacts/answer.json`:

```json
{"screen_1": 0.42, "screen_2": 0.63, "...": 0.00}
```

All seven screens must appear. Values are fractions in `[0, 1]`, and you are
scored on how close each one is.

## why this task exists

A ranked enrichment table is the standard output that decides what a lab chases
next, and the decision costs a year. The quantity asked for here is the one that
says how much of that ranking is arithmetic rather than biology — and across
these seven real studies the true answer ranges from **0.36 to 0.88**. Every one
of them was published.

The task is hard in a specific way. The obvious move is to notice that big sets
get more hits and conclude "these are all confounded, call it 0.6" — which gets
the *direction* right and the *magnitude* wrong on every screen. The spread is
the point: these studies are not equally confounded, and a method that cannot
tell 0.36 from 0.88 cannot tell a reader which ranking to trust.

Note the sizes: the seven screens have between **17 and 2,809** sets. The
smallest is the most confounded. Any approach that assumes more data means more
confounding has the sign backwards.

## scoring

Mean absolute error against the measured value, normalised against two
documented reference points:

| Strategy | MAE | Reward |
|---|--:|--:|
| Constant 0.5 for every screen | 0.1585 | 0.0000 |
| **Constant at the true mean (0.5962)** | **0.1395** | **0.0000** |
| Reference solution (`oracle/solve.sh`) | 0.0000 | 1.0000 |

Reward is `max(0, 1 - MAE / 0.1395)`, normalised against the **stronger** of the
two constant baselines — the one that already knows the right average and still
cannot tell the screens apart. Beating it requires discriminating between
screens, which is the whole task. Normalising against the weaker 0.1585 baseline
would have handed out free reward for guessing the mean.

The answer key is computed by `src/audit_screen.py` in the denali repository and
is not present in this image.

## what this task does not ask

It does not ask which sets are real, and it does not ask for a candidate list.
The quantity is a property of the **ranking**, not of any gene or pathway in it.
An answer that names a gene has misread the task.
