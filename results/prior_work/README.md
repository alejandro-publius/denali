# Prior work — PRE-EVENT, not reproducible here

These files predate the event and are **not** output of this project. They are
here for one reason: they are the evidence that our nulls are real nulls.

## The positive control

A pre-registered contrast in a 119-donor lung atlas returned **zero genes at FDR**
across three cell types, and a pre-registered rescue returned zero across four
more — **seven populations, best q = 0.124** (`scope_rescue_gradient_summary.csv`,
`primary_contrast_summary.csv`).

The same cells and the same code, run on the disease axis instead, returned
**481–6,532 genes at q<0.05** (`*__anchor_de_FULL.csv`, five populations).

**That is what makes the null a result rather than a broken pipeline.** A method
that finds nothing everywhere has proven nothing; this one finds thousands of
genes when signal exists and zero when it does not.

## Not reproducible from this repository

These require a 4.5 GB single-cell atlas that is not included. The analysis code
that produced them is in the pre-event repository,
`github.com/alejandro-publius/reversal-map`. Nothing in `results/frozen/` depends
on these files.

| File | What |
|---|---|
| `primary_contrast_summary.csv` | the null: 3 cell types, 0 genes at q<0.05, n=14/17/21 |
| `scope_rescue_gradient_summary.csv` | 7 populations, 0 genes each, best q = 0.124 |
| `*__anchor_de_FULL.csv` | the positive control, 481–6,532 genes at q<0.05 |
