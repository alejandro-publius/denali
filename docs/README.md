# Documentation index

Eighteen files is a lot to land in. Read in this order depending on what you came
to check.

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
| [`../results/sensitivity/README.md`](../results/sensitivity/README.md) | Three post-freeze checks, none pre-registered and all labelled so: the measurement/construction split, the VIF identity, and the unstressed-cell-line bound. |
| [`SCOPE_STATEMENT.md`](SCOPE_STATEMENT.md) | What is and is not claimed. |
| [`DATA_DICTIONARY.md`](DATA_DICTIONARY.md) | Every column in every frozen file. |

## If you want to know how we work

| | |
|---|---|
| [`METHOD_RULES.md`](METHOD_RULES.md) | The rules the code obeys, each one present because it changed a decision — not because it is good advice. |
| [`LIMITATIONS.md#7`](LIMITATIONS.md) §7 | Four errors we found in our own work and published, including one where we blamed a tool that works fine. |
| [`DESIGN.md`](DESIGN.md) | The visual system: seven colour tokens, four type sizes, and why the page is deliberately plain — a page arguing that most apparent discovery is artifact cannot itself look like a dashboard selling a result. |
| [`ORIGINS.md`](ORIGINS.md) | Why the project looks the way it does. |
| [`PRIOR_WORK.md`](PRIOR_WORK.md) | What predates the event, so nothing pre-built is presented as new. |

## Reference

| | |
|---|---|
| [`TOOLS.md`](TOOLS.md) | Every sponsor tool at its tested status, including the declined ones and why. |
| [`SREBF2_EVIDENCE.md`](SREBF2_EVIDENCE.md) | The positive control in full, including where it fails. **A control, not a discovery.** |
| [`GATE_C1_PREREGISTRATION.md`](GATE_C1_PREREGISTRATION.md) · [`GATE_C1_RESULTS.md`](GATE_C1_RESULTS.md) | The measurability gate that selected the first program, pre-registered and then scored. |
| [`HELDOUT_PROGRAM.md`](HELDOUT_PROGRAM.md) | The held-out program, named before the scoring code existed. |
| [`DEMO.md`](DEMO.md) | The spoken demo, under three minutes. |

## Working documents, kept unedited on purpose

[`HACKATHON_PLAN.md`](HACKATHON_PLAN.md), [`MORNING_HANDOFF.md`](MORNING_HANDOFF.md),
[`NEXT.md`](NEXT.md), [`BUILD_I_II_RESULTS.md`](BUILD_I_II_RESULTS.md).

These are records of what we planned and believed at the time, not statements of
current fact. Several carry banners where a figure in them was later superseded —
the banners are there rather than a silent edit, because a plan that quietly
matches the outcome is not evidence of anything. **`TOOLS.md` and the frozen files
are the source of truth; these are not.**
