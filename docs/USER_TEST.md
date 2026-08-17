# User test — five tasks a stranger has to finish unaided

**Every claim here was produced by driving a real browser, not by reading the
markup.** The harness is [`web/user_journey.py`](../web/user_journey.py) and it
is re-runnable:

```
/Users/alexvintera/denali/.venv/bin/python web/user_journey.py --net
```

playwright lives in that interpreter rather than this repository's, because the
study reproduces without a browser and must keep doing so. `--net` additionally
times the audit page's first run, which downloads a Python runtime from a CDN;
without it that task reports SKIPPED rather than passing silently.

The tasks are written as a person would say them, not as the interface names
them. That is the point: if a task can only be described in our vocabulary, the
interface has failed before anyone starts.

---

## The thirty-second path

**Land on `audit.html`, click the example, read a verdict: 4 seconds**, including
downloading the Python runtime. No file, no reading, no decisions.

That number did not exist before this test was written, because **the page was
broken and nobody knew**. See "What driving it found" below.

## The five tasks

| | Task, in a user's words | Click path | Result |
|---|---|---|---|
| 1 | "I'm starting a screen. Where do I even begin?" | open `screen.html` → name it → say what phenotype → **Start** | **0.2 s** to a stage map and stage 1 |
| 2 | "Write down what I'd accept as a hit, before I have data" | stage 1 → two boxes → **Write it down** | **0.1 s**, hashed and timestamped locally |
| 3 | "What confound should I expect for a screen like mine?" | stage 2 → the floor table | a **range**, never a number |
| 4 | "Is there anything to run at transduction?" | stage 5 | **"denali has nothing for you at this stage"** |
| 5 | "I was away three months. What was I doing?" | reopen `screen.html` | resumes on the stage you left, naming it |

Task 4 is a task the tool is supposed to **fail**, and it is in the list for that
reason. Seven of the eleven stages answer it the same way. A companion useful at
every stage would be trusted at none.

## What driving it found that reading it did not

Four defects, none of which any existing suite could see.

**1. `audit.html` was dead on the first click.** `core.py` grew
`from . import nulls`; the page's builder inlined a hand-written list of four
modules that did not include it, so the page assembled a `denali_audit` that
could not import itself and threw a circular-import `ImportError` at every
visitor. The drift guard compared the modules that *were* inlined against the
package and had nothing to say about one that was not. Found while trying to time
task 0. The module list is now discovered rather than written down, and two
guards were added — the page must inline every module the package has, and that
set must import itself in isolation — both mutation-tested by deleting `nulls.py`
and watching them go red.

**2. Six of the eleven stages pushed a phone viewport 65 px wide.** Every stage
that cites a source renders a long unbroken URL, and there is no `overflow-wrap`
on it by default. Found at 390 px, which is where a PI opens a link. Fixed and
re-verified on all eleven stages.

**3. One control had no accessible name** — the hidden file input behind "Load a
saved screen". Screen-reader users would have met an unlabelled control.

**4. A test bug that looked exactly like a product bug.** The seal check asserted
the string `Fingerprint` and failed, because CSS uppercases that label and
`inner_text` returns what is *rendered*. Twenty minutes were spent looking for a
`crypto.subtle` failure that did not exist. Recorded because the next person to
write a browser assertion will do the same thing.

## Where a human hesitated

The harness cannot see hesitation; these came from walking it by hand.

- **"Start" felt like a commitment.** The first screen asks for a name and a
  phenotype before showing anything, and there is no way to look first. Mitigated
  by saying "two sentences is enough, you can change all of it later" — but the
  honest fix is a browsable demo screen, and that is **not built**.
- **The stage map is eleven small boxes and the numbers are not self-explaining.**
  A first-time reader does not know that stage 5 is the expensive one. The map
  shows progress, not risk. Considered colouring the high-consequence stages and
  rejected it: it would read as a warning about *their* screen rather than about
  the stage, and this project does not decorate.
- **The floor table is the hardest thing on the page to read.** It answers "what
  should I expect" with a distribution, which is correct and is not what was
  asked. The heading above it now says to read the spread rather than the middle,
  but a reader who wants one number will still leave wanting one. That tension is
  the finding, not a defect to design away — evaluation 13 says the number does
  not exist.
- **Nobody reads "what this is not".** It sits at the bottom of the workspace in
  a tinted box, which is where such text goes to be skipped. Unresolved.

## What is still not built, and should be

Named rather than quietly omitted.

- **A comparison view.** "Is my new screen better than my old one" is the second
  question everyone asks and there is no answer on any surface.
- **A shareable permalink** encoding a result in the URL fragment, so a verdict
  can be forwarded to a PI without uploading anything.
- **A printable one-page summary** for a PI — what was found, what it means, what
  it does not say.
- **A demo screen** you can browse before committing to creating one.
- **Progressive disclosure on `audit.html`.** The verdict, the method and the
  full derivation are still one page, which serves the novice and the expert
  equally badly.
- **The stability signal is not rendered.** `audit()` now reports
  `verdict_is_stable`, and no surface shows it, so a page can still print a
  confident verdict the package itself flags as unstable. This is the most
  important item on this list.
