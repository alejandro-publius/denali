---
schema_version: "1.3"
metadata:
  author_name: "denali"
  difficulty: hard
  category: capability
  tags: ["genomics", "crispr", "confound-detection", "gene-set-enrichment", "ranking", "metascience"]
agent:
  timeout_sec: 1200
verifier:
  timeout_sec: 120
sandbox:
  cpus: 1
  memory_mb: 2048
---
# denali-size-carried

## prompt

`data/` holds seven gene-set enrichment results from seven **real, published**
studies — CRISPR knockout, CRISPRi, CRISPRa, single-cell, organoid, primary human
T cell, and bulk RNA-seq. Each `screen_N.csv` is the table such an analysis
already produces:

```
set,size,hits
cellular macromolecule biosynthetic process (GO:0034645),314,42
glycolytic process (GO:0006096),29,14
```

`size` is how many genes were measured in that set. `hits` is how many came back
significant.

`data/ranked_top10.json` gives you, for each screen, the **top 10 entries ranked
by hit count** — the list a reader of that paper would actually be looking at:

```json
{"screen_1": [{"rank": 1, "row": 812, "set": "...", "size": 314, "hits": 42}, ...]}
```

`row` is the 0-based row of that entry in the screen's CSV. Ranks are pinned for
you rather than left to be re-derived, because hit counts tie and one screen has
two sets with the same name; `rank` and `row` are the only identifiers that are
unambiguous.

**Task.** An entry is **size-carried** when its place in the top 10 is owed to how
big the set is rather than to how much came back. For each screen, decide which
of its ten entries are size-carried.

Write `/logs/artifacts/answer.json` — for each screen, the list of ranks you
claim are size-carried:

```json
{"screen_1": [1, 2, 4], "screen_2": [], "...": []}
```

All seven screens must appear. An empty list is a legitimate answer and means
you claim nothing in that top 10 was carried by size. Ranks are integers 1–10.

## what "size-carried" means, precisely

The grader's definition, stated in full so that nothing here is a guess about
intent:

> Fit `log10(1 + hits)` against raw `size` across **every** set in that screen.
> Re-rank all sets by the residual of that fit — how far each beats what its own
> size predicts. An entry is **size-carried** if it is in the top 10 by hit count
> and **not** in the top 10 by residual.

Two details that decide the answer, and are stated because guessing them is not
the skill being tested:

- The fit is over **all** sets in the screen, not just the ten. A regression fit
  on ten points is a different and much noisier line.
- `size` enters **raw**, not logged, while hits are on a `log10(1+x)` scale. The
  asymmetry is deliberate: a set with twice the genes gets roughly twice the
  chances, which is linear in size, and compressing that axis measures a weaker,
  different thing.

## why this task exists

The ranked table is what decides where a lab spends the next year, and this is
the question nobody asks of it. Across the seven screens here, **47 of the 70
top-10 entries are size-carried**, and one screen loses all ten. Every one of
these studies was published.

The task is hard in a specific way. Because most entries are carried, the shortcut
is to say so about all of them — and the scoring is built so that this earns
exactly zero. Answering "all ten, every screen" and answering "none, every screen"
both score **0.5000 balanced accuracy and reward 0.0000**, by construction. Only
telling the carried entries apart from the surviving ones pays.

The screens are not equally affected: one loses 10 of 10, another loses 2 of 10.
A method that cannot tell those two apart cannot tell a reader which published
ranking to trust.

## scoring

Every one of the 70 entries is a binary decision, pooled across all seven
screens, graded against the size-aware residual defined above.

**Reward = `max(0, 2 × balanced_accuracy − 1)`**, where balanced accuracy is the
mean of sensitivity (carried entries correctly called) and specificity (surviving
entries correctly left alone).

| Strategy | Balanced accuracy | Reward |
|---|--:|--:|
| Call every entry size-carried | 0.5000 | 0.0000 |
| Call no entry size-carried | 0.5000 | 0.0000 |
| Call the largest 30% of each top 10 carried | 0.6910 | 0.3821 |
| Call the lowest hits-per-gene 70% carried | 0.6975 | 0.3950 |
| Call the largest 70% of each top 10 carried | 0.7623 | 0.5245 |
| Reference solution (`oracle/solve.sh`) | 1.0000 | 1.0000 |

Balanced accuracy rather than accuracy or F1 because the classes are unbalanced
47/23, and every metric that ignores that hands most of the reward to whichever
constant matches the majority. The size heuristics are listed because they are
what a careful agent reaches for without running the correction, and they get
roughly half credit — right about the direction, wrong about which entries.

Grading is deterministic and runs in code. No model judges this task.

## what this task does not ask

It does not ask which entries to chase, and an answer that reads as a candidate
list has inverted the task. Identifying the size-carried entries says which parts
of a published ranking are **least** supported by its own data. The surviving
entries are not thereby endorsed — they survived one correction for one confound,
which is a much smaller claim than being real.

No gene is named in this task, and none should be named in an answer. The unit
throughout is the gene set.
