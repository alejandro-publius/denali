# Deck and video — the shot list

**The talk is `docs/DEMO.md`.** This file is only *what is on screen while it is
spoken*, and the order is locked to the beats there. If the two disagree,
`DEMO.md` is the script and this is stale.

**The deck is the live page.** Not slides — the hosted page at
`alejandro-publius.github.io/denali/`, driven by anchor links. Rebuilding the
content as slides would create a second surface that can drift from the data,
which is the failure this project exists to catch. Three PNG title cards carry
the beats the page has no section for; everything else is the real artifact.

Every anchor below is checked by the invariant suite — if a heading id is
renamed or dropped, the build fails rather than the demo doing so.

---

## Shot list

| # | Beat | On screen | Jump to |
|---:|---|---|---|
| 0 | OPEN | Title card 1 — *ten evaluations · seven negative · all ten reported* | — |
| 1 | What it is | FIG 1, the matrix | `denali/#findings` |
| 2 | **The loop** | **The agent panel, live. Press Run.** | `denali/#loop` |
| 3 | Negative one | FIG 3 | `denali/#findings` |
| 4 | Negative two | FIG 2 | `denali/#findings` |
| 5 | Negative three | Title card 2 — the heme row: highest prediction, one measured gene, zero hits | — |
| 6 | The positive | The 17-gene rank distribution, both tails | `denali/#positive` |
| — | CLOSE | Title card 3 — the repo URL, big | — |
| Q&A | held in reserve | the program table; the tools table | `denali/#table`, `denali/#tools`, `denali/#limits`, `denali/#cost` |

**Beat 2 is the only live interaction.** Everything else is scrolling to a
section that is already rendered. That is deliberate: one thing can go wrong on
stage, not seven.

### Beat 2, precisely

1. Land on `#loop`. The panel is already there — do not scroll past it and come back.
2. Press **Run** once. Do not narrate the loading; say the policy line while it runs.
3. Let it **halt on its own.** Do not press stop. The halt is the beat.
4. Point at the overstatement line — *stopping early overstated its own answer by 0.081* — and say that sentence out loud. It is the single most on-track sentence in the talk.

**Measured on the deployed page**, default settings (policy `coverage`,
tolerance `0.01`):

| | |
|---|---|
| Idle → `HALTED` | **4.2 s** |
| Stops at | **10 of 50 visited** |
| Reports | R² **0.863** on what it read · **0.782** over all 50 · gap **0.081** |
| Log | 55 lines; the overstatement sentence is in the last six |
| External fetches | **0** · JS errors **0** |

Four seconds is long enough to keep talking through and short enough that you
must not pause for it. **Say the policy sentence while it runs**, and it will
halt roughly as you finish.

If it has not halted by ten seconds, say *"it halts at ten of fifty — here's the
recorded run"* and cut to `docs/img/agent-loop.png`. **Do not press Run twice in
front of judges.**

---

## Title cards — three, all text

Build them in the page's own type and palette so they do not read as a different
project. No stock imagery, no logos but ours.

| Card | Content | Why it is a card and not the page |
|---|---|---|
| **1 · Open** | `TEN EVALUATIONS` / `SEVEN NEGATIVE` / `ALL TEN REPORTED` | The page opens on the finding; the talk opens on the posture. |
| **2 · Heme** | *Highest predicted. One measured gene. Zero hits.* — with the program name | The strongest beat is one row, and the table view buries it among fifty. |
| **3 · Close** | `github.com/alejandro-publius/denali` — and nothing else | A judge writing the URL down needs it legible from the back of a room. |

---

## Video — 3:00 hard ceiling

Screen recording with voiceover. No talking-head, no b-roll, no music bed under
speech.

**Record in this order, which is not the play order:**

1. **Beat 2 first, several takes.** It is the only live one and the only one that
   can fail. Keep the take where the halt lands cleanly.
2. **The static scroll beats in one pass** — 1, 3, 4, 6 — then cut.
3. **Voiceover last, over the locked picture.** Reading to picture keeps the
   timing honest; timing to a script and hoping the picture fits does not.

**Settings that matter:** record at 1440×900 or larger and export 1080p; browser
at 100% zoom, not the 125% that makes the type look designed for a demo; hide
bookmarks, extensions and notifications; use a fresh profile so no autocomplete
drops a real email into a URL bar on camera.

**Say the number, don't just show it.** A judge half-watching at 2× hears
"seven of ten came back negative" and stops scrubbing.

### Checklist before upload

- [ ] Under 3:00
- [ ] The halt is visible and un-cut in beat 2
- [ ] "Seven of ten" is audible in the first 15 seconds and the last 15
- [ ] No gene named that isn't the recovered known control
- [ ] URL legible in the final frame for at least 4 seconds
- [ ] Watched once at 2× with sound off — the beats still read
- [ ] Link opens in a logged-out browser

---

## What is deliberately not in the deck

- **No architecture diagram.** It is in the README for readers; on stage it costs 20 seconds and lands nothing.
- **No sponsor-tool montage.** `docs/TOOLS.md` is stronger *because* it lists what we set up and declined, and that nuance dies in a logo grid.
- **No roadmap slide.** Ten evaluations with seven negatives is the claim. A future-work slide invites "so it doesn't work yet."
- **No "built in N hours."** House rule, and it makes the work sound like a stunt.
