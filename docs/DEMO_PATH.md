# The demo path — the exact click sequence to record

Every step below was driven in a real browser (Chromium and WebKit, 1200 px and
390 px) before this file was written, and the assertions in
`/private/tmp/.../harden.py` are the same 75 checks that gate it. Nothing here
is a plan; it is a transcript of what the page does.

**The point of this document:** the demo used to narrate a paper, then a CLI.
It can now show someone USING the tool. If any step below needs narration to
paper over a gap, that is a bug, not a script note.

## Before recording

- `git pull && make test PY=.venv/bin/python` — **556** invariants, **47**
  cross-surface, **20** page-parity. All must pass. Each suite counts itself and
  prints its own total, so read the totals it prints rather than trusting these;
  the invariants figure is checked against the suite by
  `tests/test_frozen_invariants.py`, and it said 474 for long enough to be wrong
  by 78.
- Open `index.html` **from the local file** (`file:///…/denali/index.html`) or
  from the Pages URL. Both work; the local file is the safer demo because it
  proves the offline claim on camera.
- Window at 1200 × 900 or wider. Zoom 100%. Nothing else needs to be open —
  no terminal, no editor, no network.
- Do **not** pre-run the audit. The empty state is part of the story.

## The sequence

| # | Action | What appears | Why it is in the cut |
|---|---|---|---|
| 1 | Land on the page, do not scroll | Hero: "Bigger gene sets win, and it has nothing to do with biology", the crime-count analogy, **46.5%** | The claim, in one sentence, before any interface |
| 2 | Stay still ~2 s | Under the hero: **Run the audit on our screen** (the one accent button on the page) and *or drop your own results* | There is now an action above the fold. This is the change |
| 3 | **Click "Run the audit on our screen"** | The result area fills below the drop zone | One click, no install, no file, no account |
| 4 | Let the eye land on the verdict | **CONFOUNDED** — "46% of the variance in this ranking is predicted by how the sets were built, with no reference to what any gene does." | The tool says it about *our own* screen |
| 5 | Read the line under it | "Do not read the top of this ranking as biology… re-rank with a size-aware statistic… the ones that move most are the ones your current ranking is least able to justify" | The verdict comes with what to do about it |
| 6 | Scroll one notch | **AGAINST THE FIELD** — "unusually confounded — worse than nine in ten published screens: 90% of 1272 published CRISPR screens are less explained by set size than yours", with the collection caveat directly beneath | An R² is not a judgement until you know what normal looks like |
| 7 | Scroll one notch | **WHAT LEAVES YOUR TOP 10** — "Of your top 10, 3 hold their place once set size is accounted for and 7 do not" | Statistic becomes decision |
| 8 | **Stop on the table row `Myc Targets V1`** | `194 · 5707 · 1 → 24 (−23)` | **The money shot.** The largest set in the collection, our own number one, falling twenty-three places once you ask how many hits a set that size returns anyway |
| 9 | Let the last line show | "Not a candidate list. This says which entries were carried by size, not which to chase." | The tool refuses to nominate, on screen, unprompted |

Steps 1–9 are the whole demo and run in well under three minutes. Steps 10–12
below are optional, in priority order, if time remains.

## Optional continuations

10. **Their data, not ours.** Drag any recognised export onto the drop zone —
    `packages/denali-audit/tests/fixtures/mageck_gene_summary.txt` is a real
    MAGeCK file. It reads as `MAGeCK (gene_summary)` with the note explaining
    that each gene is read as a set of its sgRNAs. Shows the tool meets people
    at the file they already have.
11. **It refuses rather than guesses.** Drop
    `fixtures/mageck_sgrna_summary.txt` (the per-guide file, the wrong one).
    The page answers: *"This looks like MAGeCK's per-guide file… point it at
    gene_summary.txt from the same `mageck test` run."* An error that names
    the fix.
12. **The constant-size case.** Drop `fixtures/mageck_gene_summary_constant.txt`
    → **UNDETERMINED**, with "This is not an all-clear" in the copy. A tool
    that could have claimed a pass and does not.

## Facts a narrator may state, all verified

- Nothing is uploaded. The page makes **zero network requests** — asserted in
  the invariant suite and re-verified in-browser during the run above (the
  request log is empty of anything that is not `file:`/`data:`/`blob:`). Pull
  the wifi before recording if you want it on camera.
- The number the page computes is the number the CLI computes: **0.4649,
  CONFOUNDED, 90th percentile, 3 of 10 holding** — `tests/test_page_audit_parity.py`
  runs the page's own JS against the Python package on nine fixtures and fails
  the build on any disagreement.
- The example is our own screen: the same `(name, size, hits)` triples as
  `results/frozen/program_summary.csv`, re-exported in g:Profiler's shape.
  That equality is a test, not a claim.

## What NOT to say

- Do not call the size-aware column a better ranking, a candidate list, or a
  set of hits. It reports what the original ranking cannot justify. The page
  says so in its own last line; do not contradict it out loud.
- Do not name a gene as a finding. Program-level only, everywhere.
- Do not claim the page "runs the package" — `audit.html` does that with
  Pyodide. `index.html` runs a parity-gated port. Both are true statements;
  they are different statements.

## The other surface

`audit.html` (separate page, added the same day) runs the actual Python package
in the browser via Pyodide. It is the right demo for "the browser answer IS the
command-line answer, byte for byte", and it needs the network for a ~14 MB
one-time fetch. `index.html`'s runner is the right demo for "this cannot fail in
front of you" — instant, offline, zero requests. **For a recorded demo on
unknown wifi, use `index.html`.** If the venue network is known-good and the
point being made is fidelity, `audit.html` is the stronger claim.
