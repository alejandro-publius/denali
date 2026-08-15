---
schema_version: "1.3"
metadata:
  author_name: "denali"
  difficulty: medium
  category: capability
  tags: ["genomics", "crispr", "confound-detection", "measurement-artifact"]
agent:
  timeout_sec: 900
verifier:
  timeout_sec: 120
environment:
  cpus: 1
  memory_mb: 2048
---
# denali-gate-trap

## prompt

You are given `data/programs.csv`: 50 human gene programs from a genome-scale
CRISPRi screen in K562 cells. For each program you can see only how well it was
*measured* — how many of its declared genes were detected, how strongly they are
expressed relative to the transcriptome, how variable they are, and how
essential they are.

You cannot see the screen's results.

**Task.** For each of the 50 programs, predict whether at least one of the 9,837
knockdowns significantly moved it (BH-corrected q < 0.05).

Write your answer to `/logs/artifacts/answer.json` as a flat object mapping every
program name to `true` or `false`:

```json
{"HALLMARK_ADIPOGENESIS": true, "HALLMARK_ANGIOGENESIS": false, "...": false}
```

All 50 programs must appear. You are scored on **balanced accuracy**, so
answering everything `true` does not help.

## why this task exists

The obvious approach is a quality filter: require that a program is well
measured — most genes detected, expressed above average, variable above average
— and predict a result only for those.

That filter is wrong 20 times out of 50 on this data, always in the same
direction. Poorly-measured programs return real results anyway. A filter tuned
for measurement quality discards them, and the balanced accuracy of that
approach is **0.6981** with 20 false negatives and 1 false positive.

Beating it means noticing that measurability predicts how *much* signal a program
shows, not *whether* it shows any.
