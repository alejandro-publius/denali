# The user journey — mapped before any code, then audited for breaks

Written 2026-08-16, after docs/RESEARCH_UX.md and before any build. The user
here is the one the tool is for: a screener, not a judge. Judges get their own
path (`make judge-check`) and it works; this document ignores them.

## Who arrives, holding what

A biologist finished a CRISPR screen weeks or months ago. They ran MAGeCK (or
BAGEL, or drugZ) and then an enrichment tool — Enrichr, g:Profiler, DAVID,
clusterProfiler, fgsea, GSEA — and now hold a ranked table of gene sets. The
top of that table is about to cost them a year and six figures. Someone sent
them this page, probably with one sentence of framing ("check your ranking
before you commit").

What they know: their own screen, their enrichment tool's output format, what
a p-value is. What they may not know, and the page must not assume: what a
"Hallmark program" is, what "K562" is, why set SIZE would inflate a ranking,
what an R² is doing in a sentence, what "CRISPRi" adds over "CRISPR". They
will not read a methods section. They have a file, or can get one in two
minutes from the tool they already use.

## The journey, step by step

Each step: what they see / what they do / what can confuse them / what they
must already know for the step to work.

### 1 · Land

- **See:** wordmark, hero claim ("Bigger gene sets win, and it has nothing to
  do with biology"), the crime-count analogy, 46.5%.
- **Do:** read. There is nothing else to do — the first interactive element is
  several screens down. **(This is the break. See Dead end A.)**
- **Confusion risk:** "50 Hallmark programs scored against 9,837 CRISPRi
  knockdowns in K562" is five proper nouns in one clause. The analogy sentence
  before it carries the idea for a reader who has none of them; the risk is
  acceptable because the analogy comes first.
- **Must already know:** nothing, IF they trust the analogy. The hero works.

### 2 · Decide "does this apply to me?"

- **See:** today, nothing answers this until the "Use it on your own screen"
  section far down the page, where tool names finally appear.
- **Do:** scroll and hope.
- **Confusion risk:** a g:Profiler user has no way to know, above the fold,
  that their exact export is understood. The list of recognised formats — the
  single strongest "this applies to you" signal the project owns — is buried
  in a `<p class="note">` under a CLI block.
- **Must already know:** currently, that "your analysis already produced a
  table" refers to THEIR tool's output. **(Dead end B.)**

### 3 · Try it without commitment

- **See:** today, `pip install -e packages/denali-audit` — which assumes a
  cloned repo, a working Python ≥3.10, and comfort with pip. For a wet-lab
  biologist every one of those is a wall.
- **Do:** today: leave, or forward the link to a computational colleague
  (which is a real path, but not one the page should force).
- **Confusion risk:** `pip install -e` on a path only exists inside a clone;
  a reader who tries it verbatim in a terminal gets an error. The page's first
  actionable instruction fails for anyone who didn't clone first.
- **Must already know:** git, pip, PATH. **(Dead end C — the biggest.)**
- **After the build:** one click on "Run it on our screen" produces the full
  three-output result in the page; the CLI becomes the second copy of the
  path, not the only one.

### 4 · Run it on their own data

- **See:** today, nothing — there is no input surface on the page at all.
- **After the build:** a drop zone that speaks Morpheus's sentence ("nothing
  leaves this page — the file is read in your browser, no upload, no
  account") and lists the recognised formats by tool name, so recognition
  ("that's MY tool") happens before any file is chosen.
- **Confusion risk:** the file they drop is the wrong one (MAGeCK per-guide
  file instead of gene_summary; BAGEL `pr` instead of `bf`). The CLI already
  has named near-miss messages for exactly these; the page must show the same
  words, in the error state, with the fix ("point it at gene_summary.txt from
  the same run").
- **Must already know:** which file their tool wrote. The near-miss messages
  carry them the rest of the way.

### 5 · Read the verdict

- **See:** CONFOUNDED / PARTIALLY CONFOUNDED / NOT SIZE-DOMINATED /
  UNDETERMINED, with the one-sentence reading underneath ("46% of the
  variance in this ranking is predicted by how the sets were built…").
- **Confusion risk #1:** an R² means nothing alone. The percentile line
  against 1,272 published screens ("90% of published screens are less
  explained by set size than yours") is what converts the number into a
  judgement — it must come second, immediately, every time.
- **Confusion risk #2:** UNDETERMINED (constant set size) reads as an error.
  It is a finding, and its copy already says so; the page must render it at
  the same visual weight as the other verdicts, not as a failure state.
- **Must already know:** nothing, if the reading sentence and percentile do
  their jobs.

### 6 · See what it means for THEIR top ten

- **See:** the rerank table — which entries hold, which fall, and by how much
  ("MYC_TARGETS_V1, 194 genes, 1 → 24").
- This is the step that converts a statistic into a decision. A verdict says
  "your ranking has a problem"; the rerank table says "these specific rows
  are the problem". Order matters: verdict → percentile → rerank, always.
- **Confusion risk:** reading the size-aware column as the TRUE ranking, i.e.
  as a candidate list. It is the tool's one forbidden reading and the copy
  around the table must carry the negative claim every time it renders:
  "which entries the original ranking is least able to justify — not which
  to chase."
- **Must already know:** nothing; the table's own columns teach it.

### 7 · Leave with something

- **See:** the CLI install for repeated/scripted use, the MCP wiring for
  agents, the repo link.
- The page path is for the first run; anyone who wants the check in their
  pipeline graduates to `pip install denali-audit`. The page should say
  exactly that — the CLI is the same math, the page is the same tool.

## The dead ends, named

- **A. The page argues, then stops.** No action above the fold; first
  interactive element is the agent explorer, several screens down, and it
  explores OUR data, not yours. Fixed only by a primary action in the hero
  area.
- **B. "Does this apply to me?" is answered too late.** Tool names (the
  recognition trigger) appear only inside the CLI section's fine print.
- **C. The only "try it" path assumes a cloned repo and Python.** `pip
  install -e packages/denali-audit` fails verbatim outside a clone. The
  in-page runner removes the wall; the copy should also switch the CLI line
  to a `pip install denali-audit` form — **which does not work yet**: the package is not on PyPI and `docs/RELEASE.md` records the upload as a human decision that has not been made. Until it is, the honest line is the clone.
- **D. A user with data RIGHT NOW has no input surface.** No upload, no
  paste, nothing. This is the largest single absence and the whole of Phase
  4b/4c.
- **E. No state for failure.** A wrong file, an unrecognised format, a
  too-small table — today these paths don't exist, so their states don't
  either. The CLI's error strings (near-miss messages, MIN_SETS refusal,
  UNDETERMINED) are already written in the right voice; the page states must
  reuse them verbatim.

## What the fixed journey must feel like

Land → the hero still argues (nothing about the study is demoted) → one
button runs our own screen through the tool in the page → verdict, percentile,
rerank appear in that order → "now drop yours" is the next thing the eye
falls on → the drop zone names the eight tools it reads → any failure names
its fix → the CLI paragraph closes: same math, install it when you want it
in a pipeline.

The test of done, from the Phase 6 brief: land, click the example, watch
MYC_TARGETS_V1 fall from 1st to 24th, without narration papering over a gap.
