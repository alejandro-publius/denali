# Design system

The visual language of the results page, written down so the two surfaces stop
drifting apart. Adapted from Rachel's Figma Make study; every number, figure and
sentence rendered in it is ours, from `results/frozen/`.

There are two renderers of the same frozen data — `index.html` (static, built by
`src/build_page.py`) and `app.py` (Streamlit). They currently use **different
palettes**: the static page uses warm neutrals, the Streamlit page uses cool
Tailwind greys. This document is the target both should converge on. Converge
deliberately, not in a hurry.

---

## The idea behind it

The page argues that most of what looks like discovery is measurement artifact.
A page making that argument cannot itself look like a dashboard selling a result.
So: **paper, not product.** Hairline rules instead of cards. One accent, spent
twice. No gradient, no shadow, no rounded corner, no dark hero, no chart junk.

The restraint is the argument. If the page looked exciting, it would be making a
claim the data does not support.

## Colour

Eight tokens. Nothing outside this list appears on the page.

| Token | Value | Job |
|---|---|---|
| `--ink` | `#1a1a1a` | Body text. Near-black, not `#000` — pure black on white is harsh at body size and reads as default rather than chosen. |
| `--soft` | `#6B7280` | Secondary text, captions, labels. |
| `--rule` | `rgba(27,42,74,.14)` | Every hairline. Navy-tinted and alpha rather than a flat grey, so it sits correctly on `--paper`, `--fill` and `--tint` alike. |
| `--fill` | `#f5f7f9` | Figure ground, code ground, and the halted state. One step off paper. |
| `--navy` | `#1B2A4A` | Structure: headings, the masthead, the footer. Carries hierarchy so the accent does not have to. |
| `--tint` | `#E6F7F2` | Card ground. The accent at low saturation, used as a surface rather than as a mark. |
| `--paper` | `#fff` | Ground. |
| `--accent` | `#1D7C65` | Teal. Links, the metric numerals, and small highlights — **sparingly**. It is the only saturated colour on the page and it marks things you can act on or read a number off. Structure is `--navy`'s job, not the accent's. Darkened from `#2EC4A0` for contrast — see below. |

Semantic colour in figures (`#b2182b` red, `#2166ac` blue) comes from
ColorBrewer's diverging scale and is **only** used inside matplotlib output on
index.html, never in its page chrome. It signals direction in data, not emphasis
in text.

**app.py's status palette.** The Streamlit page carries a semantic status set in
chrome that the static page does not: `#1a7f37` (ok / green), `#9a6700` (warn /
amber) and `#b2182b` (fail / red) on the tool-chain strip, plus that red and
`#2166ac` (blue) marking the loop's null / hit / miss branches. Like the figure
colours these signal state, not emphasis, and they are the only non-token hexes
the design invariants permit on that surface.

**Radius is `8px`.** Set once in `:root` as `--radius` and applied to the elements
that read as surfaces — metric and card grids, figures, code blocks, tables. It is
deliberately *not* applied with `*`, because a non-zero radius on the universal
selector rounds every hairline and rule on the page as well.

> **Changed 2026-08-15.** This section previously specified a warm-neutral palette
> (`--ink:#1c1c1a`, `--accent:#4a6fa5`) and `0px` radius, argued as "paper, not
> product — the restraint is the argument". That was a real position and it is
> recorded here rather than overwritten silently. It was superseded by the denali
> brand system. The restraint argument still governs everything below: no gradient,
> no shadow, no dark hero, no chart junk, and failures set at the same size as
> successes. What changed is the palette and the corner, not the posture.

## Contrast — measured, not asserted

**Re-measured 2026-08-16 against the rendered page, not the token table.** The
previous version of this section scored the *warm* palette — `#1c1c1a`,
`#8c8c89`, `#a3a39b` — which `index.html` stopped using at the brand pass. It
was describing a page that no longer existed, and it took an automated sweep
over computed styles to notice. That is the same class of error this project
keeps finding elsewhere, and it is recorded rather than quietly overwritten.

Method: walk every element with a text node on the built page, take the computed
colour and the nearest opaque background, and apply the WCAG 2.1 threshold for
that element's actual rendered size and weight. Not the token table — the pixels.

### `index.html`, current palette

| Token | on `--paper` | on `--fill` | on `--tint` | verdict |
|---|---:|---:|---:|---|
| ink `#1a1a1a` | 17.40 | 16.21 | 15.71 | passes everywhere |
| navy `#1B2A4A` | 14.22 | 13.24 | 12.83 | passes everywhere |
| soft `#6B7280` | 4.83 | 4.50 | 4.36 | passes AA body on paper and fill |
| accent `#1D7C65` | 5.09 | 4.74 | 4.60 | passes AA body everywhere |

**Two failures were found and both were fixed rather than accepted.**

- **`--accent` was `#2EC4A0`, which scored 2.21 on white** and failed AA at every
  size — including the footer link carrying the repository URL, which is the one
  string on the page a reader is most likely to copy or read off a screen.
  Darkened to `#1D7C65`: **identical hue (165.6°) and saturation (0.62)**, only
  lightness moved (0.475 → 0.300). It is the same teal, and it now clears 4.5 on
  all three grounds the page uses.
- **`--soft` on `--tint` measured 4.36 against a 4.5 requirement** — the card
  headings, the only place those two met. Changed to `--navy` (12.83 there). A
  card heading reading stronger than its own body was the better call anyway.

**`--soft` on `--tint` remains the one pair to watch.** It is 4.36, and it is
fine only because nothing renders text in that combination any more. If a future
card puts secondary text on the tint ground, that is the bug this table exists
to catch.

The sweep is reproducible and finds zero failures on the current page:

```bash
node /tmp/contrast.mjs   # walks computed styles, prints every pair below threshold
```

### `app.py` — known drift, still the warm palette

`app.py` was not converged at the brand pass and still carries `#1c1c1a`,
`#8c8c89`, `#a3a39b`, `#f2f2f0`. Those four are grandfathered **by name** in the
invariant suite, so the exception is enumerated rather than waved through and
dies the moment the Streamlit view is converged. Their measured ratios on white:
ink 17.1, soft 3.4, faint 2.5.

The constraint that makes that safe is unchanged and is the real invariant:
`--soft` renders only secondary text — captions, labels, provenance — never body
copy; `--faint` is used only for non-text hairlines and large decorative
numerals. **No token below 4.5 : 1 is applied to body text on either surface.**

### Print

Both surfaces are dark text on white with no full-bleed dark block, so a
browser print or PDF stays legible and spends no ink on backgrounds. The one
accepted risk is a wide table clipping at page width: `overflow-x:auto` handles
it on screen and a printer cannot scroll.

## The page as a judge meets it — measured 2026-08-16

Four conditions nobody had tested until the night before submission. All four
were run against the built artifact, not asserted.

### Slow network — the single-file design holds

The page is one 1,088 KB file with every asset inlined, which sounds like the
worst possible shape for a bad connection. It is not, because of where the
weight sits:

| | offset | note |
|---|---:|---|
| `</style>` ends | 75 KB | includes all four woff2 faces, `font-display:swap` |
| `<h1 class="hero">` | 90 KB | 8.3% into the file |
| four inlined PNG figures | 91–1,077 KB | 903 KB, all **after** the hero |

Throttled to slow 3G (400 kbps, 400 ms latency) against the hosted URL:

| | |
|---|---:|
| **hero text painted** | **1.79 s** |
| explorer table populated | 7.33 s |
| document complete | 15.65 s |

**The dead interval is 1.8 seconds, not 15.** A first pass at this measurement
reported 15.5 s and was wrong: it timed `domcontentloaded`, which waits for all
1,088 KB to parse, rather than when anything is actually on screen. The
distinction matters because it is the difference between "this design is broken
on venue wifi" and "this design is fine", and only one of those is true.

Nothing here needs fixing. If it ever does, the lever is the 903 KB of figures,
not the 75 KB head — and moving them out of the file would cost the zero-network
property, which is worth more than four seconds of figure loading.

### Safari / WebKit

Tested in WebKit at 1200 px and 390 px, not just Chromium — it is a Mac room.
No overflow at either width, one `h1`, all 50 explorer rows, inlined Poppins
resolves (so the woff2 data URIs work), zero broken images, the agent reaches
`HALTED`, keyboard `Enter` selects a row, and **zero page errors or console
errors**.

### Fully offline

Every non-`file:`/`data:` request aborted at the network layer: zero requests
were even attempted, because there are none to attempt. 50 rows, agent halts,
detail panel populates, no broken images, fonts loaded. Clone the repo and
double-click `index.html` and the page is complete.

### Print

A4 PDF renders at 1.19 MB with nothing wider than the 794 px print column, so no
table clips and no code block splits. The clipping risk noted above does not
currently occur.

## Type

Four sizes, and a fifth only for the hero. Anything else is drift.

| Role | Size | Face |
|---|---|---|
| Hero | `clamp(2.5rem, 5.1vw, 4.25rem)` | sans, 600, `-.025em`, navy |
| Heading | `1.25rem` / 600 | sans, navy |
| Claim | `1.1875rem` | serif, max 46em |
| Body | `1rem` / 1.62 | serif |
| Small | `.8125rem` | serif or mono depending on role |

**Three families, each with one job:**

- **Sans** — `"Poppins", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif`
  — the brand voice: masthead, hero, headings, metric numerals. Nothing else.
- **Serif** — `"Source Serif 4", Georgia, "Times New Roman", serif` — all prose.
  Kept because the page is read, not scanned, and the argument lives in the prose.
- **Mono** — `"JetBrains Mono", ui-monospace, SFMono-Regular, Menlo, monospace` —
  anything a machine produced or a person would type: evidence lines, the footer,
  hashes, commands, `tabular-nums` columns.

The split is headline versus prose versus machine output. Sans names the project,
serif argues it, mono shows the receipts.

All three are vendored as latin-subset `woff2` under `assets/fonts/` and inlined
into the page as base64 `@font-face` sources. Not a CDN: the no-network invariant
means the page has to render as designed on a machine with no wifi. Before this,
the page *named* Source Serif 4 and JetBrains Mono but never actually loaded
them, so it had been silently falling back to Georgia and Menlo.

The mono/serif split does work here: when the agent prints `n=76 members · hits
95 · R_p 1.982`, the monospace says *this came out of a file* without a label
saying so.

## Layout

- **Hairline-ruled column**, max width `1100px`, `44px 0 96px` padding.
- **Sections are separated by a `1px` rule, not by whitespace.** Whitespace
  separation reads as slides; rules read as a document.
- **Shared-rule grids.** Metric and card grids are built as `gap:1px` over a
  `--rule` background, so cell dividers are the grid's own background showing
  through. No floating boxes, no borders that double up.
- Running text stays under about 65 characters. Tables and code get
  `overflow-x:auto` on their own container so the page body never scrolls sideways.
- Numbers that line up in columns get `font-variant-numeric: tabular-nums`.
  Always. A column of digits that shifts as it updates is a bug.

## Motion

There is one animated thing on the page: the agent stepping at 420ms intervals.
It is animated because the *sequence* is the point — you are watching it decide.

Nothing else moves. No scroll reveals, no fades, no hover transforms.

## Interaction — the page as a product, not only a paper

Added 2026-08-16. Everything above this section covers a page you READ. The
audit runner (drop a CSV, get a verdict) makes it a page you USE, and a used
page has states a read page does not. The rules below extend the system; they
change nothing above.

### The accent budget — the decision, written down

The accent's declared job is "things you can act on or read a number off".
The budget was described as at its edge, and the honest question was whether
interactive elements justify raising it. **Decision: raised by exactly one
named use — `.btn.primary`, the accent-filled button, at most ONE instance on
the page.** The page now exists to get one action taken (run the audit); a
page with one purpose may mark that one purpose with its one saturated colour.
This is g:Profiler's exact spend — one orange Run button on an otherwise grey
surface — observed in docs/RESEARCH_UX.md, and it is where the budget stops:
every other new control is ink or ghost, verdict and percentile numerals reuse
the metric-numeral rule that already exists, and if a second accent button
ever appears the budget is broken, not stretched. White-on-accent measures
5.09:1 (`#1D7C65` under white text, same ratio as accent-on-paper by symmetry),
clearing AA for the button label.

### Buttons — the vocabulary, three levels and no fourth

The explorer already had `.btn` and `.btn.ghost`; this names them, adds the
one primary, and closes the set.

| Class | Ground / text | Job | Allowed |
|---|---|---|---|
| `.btn.primary` | `--accent` / `--paper` | THE page action — run the audit | exactly one on the page |
| `.btn` | `--ink` / `--paper` | a section's default action ("Run the agent") | one per section |
| `.btn.ghost` | transparent / `--ink`, `--rule` border | everything else: Step, Reset, Export, "use the example" | unlimited |

All three: mono at `.8125rem/600`, `9px 16px` padding, no radius override (the
`--radius` rule applies), no shadow, no gradient, no transform on hover.
Hover: solid buttons drop to `opacity:.84`; ghost sharpens its border to
`--ink`. Focus: the existing `:focus-visible` accent ring, 2px, offset 2px.
Active: no separate style — the state change the click causes IS the feedback.
Disabled: `opacity:.32`, `cursor:default`, and a disabled control must never
be the only path — something nearby says what enables it.

**There is deliberately no destructive level.** The page holds no user data
beyond the current in-memory run, so nothing on it can destroy anything worth
a warning colour. Reset (explorer or audit) discards an ephemeral run and
stays ghost. If the page ever gains an action that discards something a user
typed or built, that action gets a confirmation sentence, not a red button —
red stays reserved for data semantics inside figures.

### Forms and upload

- **The drop zone is the input.** One surface accepts click-to-browse, drag
  and drop, and paste — Morpheus's pattern. 1px dashed `--rule` border,
  `--paper` ground; on dragover the ground moves one step to `--fill` and the
  border to solid `--ink`. No icon library, no cloud glyph.
- **The no-upload sentence sits inside the drop zone**, not in a footnote:
  the file is read in the browser, nothing leaves the page. Stating the
  page's strongest property at the exact point of hesitation.
- **Formats are named before the file is chosen** — the tool names (Enrichr,
  g:Profiler, MAGeCK…) are the recognition trigger and belong on or beside
  the zone in `--soft` small text.
- Native `<input type=file>` is visually hidden but focusable; the zone is a
  `<label>` for it, so keyboard and screen-reader users get the native
  affordance. `<select>` controls reuse the explorer's `.ctl select` style.

### Feedback — how results, errors, and waits read

- **A result appears in place, below the input that produced it**, input
  still visible (g:Profiler). Verdict first, at metric-numeral scale; the
  percentile sentence second; the rerank table third. That order is fixed —
  it is the argument's order (what / compared to what / so what).
- **Errors are sentences, not colours.** The CLI's own strings (near-miss
  messages, the MIN_SETS refusal, UNDETERMINED) render verbatim, ink on
  `--fill`, mono, prefixed the way the CLI prefixes them. No red, no warning
  triangle iconography beyond the ⚠ the CLI itself prints. UNDETERMINED is a
  finding, not a failure, and renders at full verdict weight.
- **Empty states name their exits** (Galaxy's history panel, per the
  research): the pre-run state of the result area says what will appear and
  which two actions produce it.
- **No spinners.** Client-side parsing of a realistic CSV is far under 150ms;
  a flash-frame spinner is noise. The one operation that can take visible
  time (a many-MB file) gets a mono "reading <filename>…" line, static. The
  agent's 420ms step remains the only animated thing on the page.

## Writing

The visual restraint is worth nothing if the copy oversells.

- **State the number, then the objection.** "0.751, and the honest floor is 0.561
  because one feature is circular." Never the flattering half alone.
- **Name what a thing is not.** The control section says "this is a control, not a
  discovery" in the section itself, not in a footnote.
- **No exclamation marks, no "excitingly", no "remarkably".** If a result needs an
  adverb it is not a result.
- **Failures get the same type size as successes.** The held-out failure and the
  positive control are set identically. Nothing is visually demoted for being
  inconvenient.
- Sentences carry the caveat inline rather than deferring it to a caption.

## What is enforced in code

Not aspiration — the build fails on these:

| Rule | Where |
|---|---|
| No network call of any kind from the page | 5 patterns, `tests/test_frozen_invariants.py` |
| Figures inlined as base64, page is standalone | same |
| No gene symbol near verdict language | the scope guard |
| No seal framing, in text **or** in a figure label | text scan + figure-source scan |
| Every displayed number traces to a frozen file | `V()` in `src/build_page.py`, 49 values |
| No broken relative link | both READMEs |

## Known drift

**app.py vs the brand palette — OPEN, opened 2026-08-15.** The brand pass
(`--ink:#1a1a1a`, `--navy:#1B2A4A`, `--accent:#2EC4A0`) landed on `index.html`
and did not reach `app.py`, which still carries the previous generation of warm
neutrals: `#1c1c1a` (ink), `#8c8c89` and `#a3a39b` (soft/faint), `#f2f2f0`
(fill). Those three are **grandfathered by name** in the palette guard rather
than waved through, so the exception is enumerated and disappears the moment
app.py is converged. This is deliberately not fixed here: `app.py` is being
edited concurrently and re-paletting a file mid-edit produces a conflict, not a
design. Whoever owns that file next should map those four to the current tokens
and delete this paragraph along with the grandfather list in the guard.

**app.py cool greys — RESOLVED 2026-08-15.** `app.py` used cool Tailwind greys
(`#111827 / #6b7280 / #d1d5db / #4b5563 / #374151`) where this document specifies
warm neutrals, so the two surfaces did not read as siblings. Every grey now maps
to a declared token: `#111827`/`#374151` → `--ink`, `#6b7280`/`#4b5563` → `--soft`,
`#d1d5db`/`#e5e7eb` → `--faint`, `#fafafa`/`#f7f7f8` → `--fill`, and `#ffffff` →
`--paper`. The figure colours `#b2182b`/`#2166ac` were left untouched, being
semantic. (Phase 3 extends the design invariants to read `app.py` too, so this
cannot silently return.)
