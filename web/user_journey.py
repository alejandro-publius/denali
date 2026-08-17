"""Walk the five tasks a stranger has to complete unaided, and time them.

WHY THIS IS A SCRIPT AND NOT A PARAGRAPH. "The interface is usable" is a claim,
and every other claim in this repository is checkable. This one is too: it drives
a real browser through the real built pages and reports what happened, including
how long the thirty-second path actually takes. `docs/USER_TEST.md` is written
from its output rather than from memory.

WHAT IT DOES NOT DO. It cannot tell you where a human hesitated -- only a human
can, and the hesitations recorded in docs/USER_TEST.md came from walking it by
hand. This catches the harder-edged failures: a control with no accessible name,
a page that throws, a task that cannot be completed at all, a promise the
interface makes and does not keep.

    /Users/alexvintera/denali/.venv/bin/python web/user_journey.py [--net]

playwright lives in that venv rather than this repository's, because the study
reproduces without a browser and must keep doing so. `--net` additionally times
audit.html's first run, which downloads a Python runtime from a CDN; without it
that task is reported as SKIPPED rather than silently passed.
"""
from __future__ import annotations

import pathlib
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parent.parent
SCREEN = "file://" + str(ROOT / "screen.html")
AUDIT = "file://" + str(ROOT / "audit.html")

results: list[tuple[str, bool | None, str]] = []


def note(task: str, ok: bool | None, detail: str = "") -> None:
    results.append((task, ok, detail))


def run(want_net: bool) -> int:
    from playwright.sync_api import sync_playwright

    with sync_playwright() as pw:
        br = pw.chromium.launch()
        pg = br.new_page(viewport={"width": 1280, "height": 900})
        errs: list[str] = []
        pg.on("pageerror", lambda e: errs.append(str(e)))

        # ---- 1. start a screen -------------------------------------------
        t = time.time()
        pg.goto(SCREEN)
        pg.evaluate("localStorage.clear()")
        pg.reload()
        pg.fill("#sname", "bortezomib resistance")
        pg.fill("#spheno", "cells that survive drug at IC90")
        pg.click("#create")
        pg.wait_for_selector("#panel h3")
        note("1. start a screen and reach stage 1", True, f"{time.time()-t:.1f}s")

        # ---- 2. write down what would count as a hit, before any data -----
        t = time.time()
        pg.fill("#prehit", "4-fold depletion in treated vs untreated, both replicates")
        pg.fill("#prestop", "fewer than 3 genes clear it, or the control does not deplete")
        pg.click("#preseal")
        pg.wait_for_selector(".sealed")
        # inner_text reflects CSS text-transform, so compare case-insensitively --
        # the first version of this check asserted "Fingerprint" and failed against
        # a page that renders it uppercase, which looked like a product bug and was
        # a test bug.
        sealed = pg.inner_text(".sealed").lower()
        note("2. seal a pre-registration",
             "fingerprint" in sealed and len(pg.evaluate(
                 "JSON.parse(localStorage['denali.screen.v1']).prereg.hash")) == 64,
             f"{time.time()-t:.1f}s")

        # ---- 3. find out what floor to expect, before spending anything ---
        t = time.time()
        pg.click("button[data-n='2']")
        pg.wait_for_selector(".bins")
        txt = pg.inner_text("#panel")
        note("3. reach the design-time floor", "middle 80%" in txt,
             f"{time.time()-t:.1f}s")
        note("3a. it refuses to give a point estimate",
             "cannot tell you where your screen" in txt)
        note("3b. it surfaces the unsettled question rather than hiding it",
             "not settled" in txt)

        # ---- 4. a stage where the honest answer is "nothing" --------------
        pg.click("button[data-n='5']")
        pg.wait_for_selector("#panel h3")
        s5 = pg.inner_text("#panel")
        note("4. stage 5 says denali has nothing to offer",
             "has nothing for you at this stage" in s5)
        note("4a. the failure is in the user's terms, not the field's",
             "cannot tell which guide" in s5)
        note("4b. unverified claims are visibly marked", "NOT CHECKED" in s5)

        # ---- 5. leave and come back --------------------------------------
        pg.click("button[data-n='3']")
        pg.reload()
        pg.wait_for_selector("#panel h3")
        res = pg.inner_text("#resume")
        note("5. resuming shows what you decided and where you were",
             "you were on" in res and "stage 3" in res.lower())

        # ---- interface obligations ---------------------------------------
        unnamed = pg.evaluate(
            "Array.from(document.querySelectorAll('button,select,input,a'))"
            ".filter(e=>!e.textContent.trim() && !e.getAttribute('aria-label')"
            " && !(e.labels&&e.labels.length)).length")
        note("every control has an accessible name", unnamed == 0,
             f"{unnamed} unnamed")
        pg.set_viewport_size({"width": 390, "height": 780})
        overflow = pg.evaluate(
            "document.documentElement.scrollWidth > window.innerWidth + 1")
        note("no horizontal scrolling on a phone-width viewport", not overflow)
        pg.set_viewport_size({"width": 1280, "height": 900})
        note("the page never throws", not errs, "; ".join(errs[:2]))

        # ---- the thirty-second path, on the audit page --------------------
        if want_net:
            p2 = br.new_page()
            e2: list[str] = []
            p2.on("pageerror", lambda e: e2.append(str(e)))
            t = time.time()
            p2.goto(AUDIT)
            p2.click("#tryexample")
            try:
                p2.wait_for_selector(".chip", timeout=180000)
                secs = time.time() - t
                note("thirty-second path: land, click the example, read a verdict",
                     True, f"{secs:.0f}s including the runtime download")
                note("  the verdict is the null-relative one",
                     "NULL" in p2.inner_text(".chip").upper(),
                     p2.inner_text(".chip"))
            except Exception as exc:                              # noqa: BLE001
                note("thirty-second path: land, click the example, read a verdict",
                     False, str(exc)[:120])
            p2.close()
        else:
            note("thirty-second path (needs the CDN; pass --net)", None,
                 "SKIPPED — not silently counted as a pass")

        br.close()

    ok = sum(1 for _, o, _ in results if o is True)
    skipped = sum(1 for _, o, _ in results if o is None)
    total = len(results) - skipped
    for name, o, detail in results:
        tag = "SKIP" if o is None else ("PASS" if o else "FAIL")
        print(f"{tag}  {name}" + (f"  --  {detail}" if detail else ""))
    print(f"\n{ok}/{total} user-journey checks passed"
          + (f", {skipped} skipped" if skipped else ""))
    return 0 if ok == total else 1


if __name__ == "__main__":
    try:
        raise SystemExit(run("--net" in sys.argv))
    except ImportError:
        print("SKIP  playwright is not installed in this interpreter. Run with "
              "/Users/alexvintera/denali/.venv/bin/python — the study reproduces "
              "without a browser and this is deliberately not in `make test`.")
        raise SystemExit(0)
