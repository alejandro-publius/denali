# denali-audit

**How much of your gene-set ranking is set size rather than biology?**

A screen hands you a ranked list of pathways. Chasing one costs about a year and six
figures. Bigger sets return more hits than smaller ones regardless of what either does —
the way a raw crime count always ranks big cities as the most dangerous. This measures
how much of your ranking that explains, before you commit.

```bash
# not on PyPI yet -- install from a clone of the repository
pip install -e packages/denali-audit
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

## You haven't run enrichment yet

Enrichment is a later step, and plenty of screens never reach it. The decision — which
three hits to chase — gets made the week the screen finishes, when what you are holding
is the output of the caller itself. Those are read too:

| tool | recognised from | what a "set" becomes |
|---|---|---|
| MAGeCK | `num`, `neg\|goodsgrna` | a gene, and its sgRNAs |
| BAGEL2 | `BF`, `NumObs` (approximate — flagged) | a gene, and its guide observations |
| drugZ | `numObs`, `fdr_synth` (approximate — flagged) | a gene, and its guide observations |

The question shifts with the input. On enrichment output it asks how much of your pathway
ranking is set size; on caller output it asks how much of your gene ranking is **how many
guides survived for each gene** — the same confound one level down.

Two honest limits, both stated in the output rather than left to be discovered:

- **Neither BAGEL nor drugZ reports a count of significant guides per gene.** Genes past
  the cutoff are credited their full observation count, which is coarse. Both mappings
  are marked approximate and the CLI prints the warning above the verdict.
- **Most libraries build every gene with the same number of guides.** Size then has no
  variance, the R² is undefined, and the verdict is `UNDETERMINED` — explicitly *not* an
  all-clear. It means the question could not be asked, not that the answer was good.

MAGeCK is the exception: `num` and `neg|goodsgrna` are both exact counts, so that mapping
is not approximate. It reads the depletion direction; for enrichment, name the `pos`
columns yourself.

## Where does your ranking sit?

An R² is not a judgement until you know what normal looks like. Every audit reports a
percentile against **1,272 published CRISPR screens** (BioGRID ORCS), so a number comes
back with a reference class attached:

```
AGAINST THE FIELD
This ranking is unusually confounded — worse than nine in ten published screens:
90% of 1272 published CRISPR screens are less explained by set size than yours.
```

The field's median is **0.224**. That output is this project's own screen at **0.465** —
the tool says it about us. The reference was built against MSigDB Hallmark; if your sets
come from a different collection the percentile is indicative, not exact, and it says so.

## The correction, applied

Knowing a ranking is confounded is not the same as knowing what to do about it. This
applies the size-aware correction and shows you what moves:

```bash
denali rerank my_results.csv --top 10
```

On the screen this project was built from — 50 MSigDB Hallmark pathways against 9,837
CRISPRi knockdowns — three of the top ten hold their place and seven do not. The
number-one ranked pathway, `HALLMARK_MYC_TARGETS_V1` at 194 genes, falls to 24th.

It reports which entries the original ranking is **least able to justify**. That is the
inverse of a candidate list, and it is the only direction this tool moves in.

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

## Where this comes from

This is not a tool that resembles a study — it is the study's own code, packaged.
`core.py` is vendored verbatim from the research repository, and a test in this package
runs it against the frozen research data and requires exactly **0.4649**, the published
headline. If the tool and the paper ever disagree, CI fails rather than the two quietly
diverging.

The study behind it ran **eleven evaluations** against its own headline. **Seven came
back negative**, one returned no verdict when its own pre-registered power rule fired,
and all eleven are reported — including the one where the same check was run on 1,272
published screens and found this project's own number atypical of the field. Full
writeup, data and provenance: [github.com/alejandro-publius/denali](https://github.com/alejandro-publius/denali).
