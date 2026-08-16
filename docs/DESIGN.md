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

Seven tokens. Nothing outside this list appears on the page.

| Token | Value | Job |
|---|---|---|
| `--ink` | `#1c1c1a` | Text. A warm near-black, not `#000` — pure black on white is harsh at body size and reads as default rather than chosen. |
| `--soft` | `#8c8c89` | Secondary text, captions, labels. Same warmth as `--ink`. |
| `--faint` | `#a3a39b` | Step numbers, the quietest tier. |
| `--rule` | `rgba(0,0,0,.11)` | Every hairline. Alpha rather than a flat grey so it sits correctly on both `--paper` and `--fill`. |
| `--fill` | `#f2f2f0` | Figure ground and the halted state. Warm, one step off paper. |
| `--paper` | `#fff` | Ground. |
| `--accent` | `#4a6fa5` | A muted slate blue. **Spent exactly twice** on the original page: the pull-quote rule and the footer link. Interactive additions have extended it — checkbox accent, the proposal rail, the halt heading — and that is the budget's edge. Adding an eighth use means removing one. |

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

**Radius is `0px`, globally.** Set once in `:root` and applied with `*`. Every
corner on the page is square, and that is a decision, not an oversight.

## Contrast — a deliberate accept

Checked 2026-08-15, WCAG 2.1, each token on `--paper` (`#fff`):

| Token | Ratio | AA body (4.5) | AA large / UI (3.0) |
|---|---:|:--:|:--:|
| ink `#1c1c1a` | 17.1 : 1 | pass | pass |
| soft `#8c8c89` | 3.4 : 1 | fail | pass |
| faint `#a3a39b` | 2.5 : 1 | fail | fail |

**Accepted, with the constraint that makes it safe.** `--ink` carries every line a
reader must read. `--soft` renders only secondary text — captions, labels,
provenance — never body copy, and it clears AA for large text and UI components.
`--faint` is used only for non-text (hairline borders on `app.py`) and large
decorative numerals (step numbers on `index.html`), never a string parsed at body
size. **No token below 4.5 : 1 is applied to body text on either surface** — that
is the invariant; if `--soft` or `--faint` ever lands on running text, that is the
bug to catch. Print: both surfaces are dark text on `--paper` white with no
full-bleed dark block, so a browser print/PDF stays legible and spends no ink on
backgrounds; the one accepted risk is a wide table clipping at page width, which
`overflow-x:auto` handles on screen but a printer cannot scroll.

## Type

Four sizes, and a fifth only for the hero. Anything else is drift.

| Role | Size | Face |
|---|---|---|
| Hero | `clamp(2.5rem, 5.1vw, 4.25rem)` | serif, 600, `-.025em` |
| Heading | `1.25rem` / 600 | serif |
| Claim | `1.1875rem` | serif, max 46em |
| Body | `1rem` / 1.62 | serif |
| Small | `.8125rem` | serif or mono depending on role |

**Three families, each with one job:**

- **Serif** — `"Source Serif 4", Georgia, "Times New Roman", serif` — all prose.
  Chosen because the page is read, not scanned.
- **Mono** — `"JetBrains Mono", ui-monospace, SFMono-Regular, Menlo, monospace` —
  anything a machine produced or a person would type: evidence lines, the footer,
  hashes, commands, `tabular-nums` columns.
- No third family. The distinction is prose versus machine output, and two faces
  carry it.

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

**app.py palette — RESOLVED 2026-08-15.** `app.py` used cool Tailwind greys
(`#111827 / #6b7280 / #d1d5db / #4b5563 / #374151`) where this document specifies
warm neutrals, so the two surfaces did not read as siblings. Every grey now maps
to a declared token: `#111827`/`#374151` → `--ink`, `#6b7280`/`#4b5563` → `--soft`,
`#d1d5db`/`#e5e7eb` → `--faint`, `#fafafa`/`#f7f7f8` → `--fill`, and `#ffffff` →
`--paper`. The figure colours `#b2182b`/`#2166ac` were left untouched, being
semantic. (Phase 3 extends the design invariants to read `app.py` too, so this
cannot silently return.)
