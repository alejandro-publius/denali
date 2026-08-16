# denali-audit

**How much of your gene-set ranking is set size rather than biology?**

A screen hands you a ranked list of pathways. Chasing one costs about a year and six
figures. Bigger sets return more hits than smaller ones regardless of what either does —
the way a raw crime count always ranks big cities as the most dangerous. This measures
how much of your ranking that explains, before you commit.

```bash
pip install denali-audit
denali audit my_results.csv
```

It reads the table your tool already produced. No column renaming:

| tool | recognised from |
|---|---|
| g:Profiler | `term_size`, `intersection_size` |
| DAVID | `Pop Hits`, `Count` |
| clusterProfiler | `BgRatio`, `Count` |
| Enrichr / GSEApy | `Overlap` |
| fgsea | `size`, `leadingEdge` (approximate — flagged) |
| GSEA desktop | `SIZE`, `FDR q-val` (approximate — flagged) |

Anything else: `denali audit FILE --set <col> --size <col> --hits <col>`.

## Two screens agreed?

That's the strongest evidence most hit lists ever get. Both are confounded the same way,
so agreeing for the same wrong reason looks exactly like agreeing for the right one.

```bash
denali replication paired.csv --hits-b hits_screen_2
```

## What it will not do

It does not rank your sets, name a candidate, or tell you what to chase. It measures a
property of the ranking, not of anything in it.

## Provenance

The maths is vendored verbatim from the research repository that published it, and a test
asserts this package reproduces the published headline (R² 0.4649 on 50 MSigDB Hallmark
programs against 9,837 CRISPRi knockdowns) so it cannot drift.

Method: VIF = 1 + (m−1)ρ̄ — Wu & Smyth 2012, *NAR* 40(17):e133.
Full study: https://alejandro-publius.github.io/denali/
