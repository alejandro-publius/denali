# Prior work

**This is background, not hackathon output.** The projects below ran before the
event. They are here because they explain why this repository is built the way it
is, and because several numbers in it were first obtained during that earlier
work. Nothing in this section is presented as a result of the event.

---

## What came before

**A figure-to-value certifier, falsified by its own measurements.** The premise
was that a number read off a published figure could be admitted as evidence if
axis calibration and an aggregate invariant both passed. That turned out to be
false: aggregate invariants do not constrain individual values, because errors
cancel. A screen of 500 real open-access papers then found roughly 5% state a
quantity the method could test at all. The project was retired on its own
measurement rather than on a change of interest.

**A lung fibrosis program, retired on a pre-registered null.** The question was
whether a reproducible donor-level transcriptional program separates more- from
less-fibrotic regions of the same IPF lung, in a 119-donor single-cell atlas. The
pre-registered primary contrast returned **zero genes at FDR** across three cell
types. A pre-registered rescue across four further compartments returned zero
again — **seven populations, best q = 0.124**.

The positive control is what makes that a result rather than a failure: the same
cells and the same code, run on the disease axis, returned **481–6,532 genes at
q<0.05**. The machinery worked. The dataset did not contain the contrast the
question needed, and the criterion that ended the project had been written down
in advance.

**A cross-paper conflict engine** was retired earlier still, when its
"contradictions" turned out to be parsing and retrieval artifacts rather than
disagreements between authors.

## Leading directly into this project

Before any pipeline was built here, four candidate gene programs were put through
a measurability gate — are the program's genes present, expressed, and variable
in the perturbation substrate. **Three of the four failed**: the integrated
stress response, senescence, and the interferon response. Only the
unfolded-protein-response arm passed, and it went on to produce this project's
first null, for a reason the gate had not thought to test — the program is not
*engaged* in an unstressed cell line, only *measurable* in one.

That distinction, measurable versus engaged, is the single most useful thing the
prior work handed over, and it is recorded as a design failure in
`LIMITATIONS.md` §3.

## Methods note

Thresholds and the held-out program list were committed before the corresponding
results existed. Original repository: `github.com/alejandro-publius/reversal-map`,
pre-event. Seeds were fixed at `20260815`.

## Numbers in this repository that were first obtained before the event

Stated once here rather than repeated as caveats throughout:

| Number | Where it appears | Status |
|---|---|---|
| Gate C1 outcomes for the four candidate programs | `docs/GATE_C1_RESULTS.md` | pre-event |
| ILD null: 7 populations, best q = 0.124; positive control 481–6,532 genes | this document only | pre-event, not re-run |
| Retrieval audit: 34 sources / 113 genes, one review at 50.4%, 14/113 title matches, 19 of 20 probe genes returning the same paper | `LIMITATIONS.md` §5, `CAPTIONS.md` FIG 4 | **measured 2026-08-15, carried over dated** — the underlying indexes are live and will not reproduce exactly |

Everything else in this repository — the 50-program matrix, the predictor, the
held-out evaluation, the controls, the sensitivity check — is computed from
checksummed local files with fixed seeds, and reproduces exactly from the
commands in `MORNING_HANDOFF.md` §8.
