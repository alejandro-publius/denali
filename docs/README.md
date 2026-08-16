# Documentation index

Twenty-seven files is a lot to land in. Read in this order depending on what you
came to check.

## If you have five minutes

| | |
|---|---|
| [`LOOP.md`](LOOP.md) | The loop, drawn. Measure → model → gate → propose → audit, with the file behind each stage and the one-line grep that would prove the claim false. |
| [`LIMITATIONS.md`](LIMITATIONS.md) | What this does not claim, led by the strongest objection rather than the weakest. §0 is the finding that undercuts the simpler version of our headline. |
| [`../REPORT.md`](../REPORT.md) | The result written out, every number traced to a frozen file. |

## If you are checking whether to believe it

| | |
|---|---|
| [`MATRIX_PREREG.md`](MATRIX_PREREG.md) | The pre-registration. Hashed `d3e24b77…` and committed at `19684f2`, before the analysis it judges. Recover that exact version with `git show 19684f2:docs/MATRIX_PREREG.md` and diff it against what we reported. |
| [`../results/sensitivity/README.md`](../results/sensitivity/README.md) | Three post-freeze checks, none pre-registered and all labelled so: the measurement/construction split, the VIF identity recovering CAMERA's 2012 result from data, and the unstressed-cell-line bound. |
| [`RPE1_PREREG.md`](RPE1_PREREG.md) | The second-cell-line arm, pre-registered and hashed (`ae62feda…`) before it ran. It cleared its bar by 0.026 and the doc says why that is thin. |
| [`ANNOTATION_PREREG.md`](ANNOTATION_PREREG.md) | The annotation-scaling arm (`ec5edb90…`). Our prediction was wrong in direction **and** the power rule fired — both failures are in the result, not softened here. |
| [`OFFTARGET.md`](OFFTARGET.md) | The confound taken outside our own data, into two published clinical-adjacent off-target datasets. Post-hoc and thresholds swept, labelled so. Includes the tautology the arm refused to report and the threefold overstatement we caught ourselves making. |
| [`ADAMSON_PREREG.md`](ADAMSON_PREREG.md) · [`ADAMSON_RESULTS.md`](ADAMSON_RESULTS.md) | The engagement arm, pre-registered before the substrate was opened, plus the amendment that defines its control by construct identity and the result that followed. |
| [`CORPUS.md`](CORPUS.md) | The headline tested against 1,272 published screens from 187 publications. Post-hoc. Reports both the screen-level and publication-level shares, and discloses an independent run of the same idea that landed near 0.10 and could not be reconciled. |
| [`NUMBERING.md`](NUMBERING.md) | Why the evaluations are numbered the way they are, written when two arms both claimed 8. Number by arrival, not by importance. |
| [`SCOPE_STATEMENT.md`](SCOPE_STATEMENT.md) | What is and is not claimed. |
| [`DATA_DICTIONARY.md`](DATA_DICTIONARY.md) | Every column in every frozen file. |

## If you want to know how we work

| | |
|---|---|
| [`METHOD_RULES.md`](METHOD_RULES.md) | The rules the code obeys, each one present because it changed a decision — not because it is good advice. |
| [`LIMITATIONS.md#7`](LIMITATIONS.md) §7 | Four errors we found in our own work and published, including one where we blamed a tool that works fine. |
| [`DESIGN.md`](DESIGN.md) | The visual system: seven colour tokens, four type sizes, and why the page is deliberately plain — a page arguing that most apparent discovery is artifact cannot itself look like a dashboard selling a result. |
| [`ORIGINS.md`](ORIGINS.md) | Why the project looks the way it does. |
| [`LANDSCAPE.md`](LANDSCAPE.md) | Where this sits in the field, researched not assumed: the $28B/year irreproducibility figure, the same confound documented in three adjacent domains, and an honest note on which of them is already solved. |
| [`PRIOR_WORK.md`](PRIOR_WORK.md) | What predates the event, so nothing pre-built is presented as new. |

## Reference

| | |
|---|---|
| [`TOOLS.md`](TOOLS.md) | Every sponsor tool at its tested status, including the declined ones and why. |
| [`SREBF2_EVIDENCE.md`](SREBF2_EVIDENCE.md) | The positive control in full, including where it fails. **A control, not a discovery.** |
| [`GATE_C1_PREREGISTRATION.md`](GATE_C1_PREREGISTRATION.md) · [`GATE_C1_RESULTS.md`](GATE_C1_RESULTS.md) | The measurability gate that selected the first program, pre-registered and then scored. |
| [`HELDOUT_PROGRAM.md`](HELDOUT_PROGRAM.md) | The held-out program, named before the scoring code existed. |
| [`DEMO.md`](DEMO.md) | The spoken demo, under three minutes. **Written for an event that was not entered**, kept as a record. |
| [`LITERATURE.md`](LITERATURE.md) · [`LITERATURE_PREREG.md`](LITERATURE_PREREG.md) | Evaluation 11 — of the 187 publications behind the corpus arm, how many mention set size at all. Pre-registration sealed before the run. |
| [`DECK.md`](DECK.md) | What is on screen while `DEMO.md` is spoken. **Event not entered**, kept as a record — but the measured slow-3G and WebKit results in it are real and current. |
| [`SUBMISSION.md`](SUBMISSION.md) | Submission copy, every figure carried from `results/`. **The submission did not happen**; kept because it is the most compact prose statement of the whole project. |
| [`NUMBERING.md`](NUMBERING.md) | Why evaluation 8 is the off-target arm, and the disposition of all eleven branches. |

## Working documents, kept unedited on purpose

[`HACKATHON_PLAN.md`](HACKATHON_PLAN.md), [`MORNING_HANDOFF.md`](MORNING_HANDOFF.md),
[`NEXT.md`](NEXT.md), [`BUILD_I_II_RESULTS.md`](BUILD_I_II_RESULTS.md).

These are records of what we planned and believed at the time, not statements of
current fact. Several carry banners where a figure in them was later superseded —
the banners are there rather than a silent edit, because a plan that quietly
matches the outcome is not evidence of anything. **`TOOLS.md` and the frozen files
are the source of truth; these are not.**
