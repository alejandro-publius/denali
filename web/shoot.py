"""Re-shoot the README's screenshots from the pages as they are RIGHT NOW.

Why this exists. The two most prominent images in the README went stale twice in
one day -- once showing a command the CLI no longer used, once showing a page
two rebuilds old -- because re-shooting was a manual step nobody owned. A
screenshot is a claim about the product, and an unowned claim rots. This makes
it one command.

    .venv/bin/python web/shoot.py

audit.html is shot AFTER its example has actually run: the page loads CPython in
WebAssembly and executes the real package, so a screenshot taken before the run
completes shows an empty dropzone and proves nothing. The script waits for the
verdict text to appear and fails loudly if it never does -- a broken page must
not silently produce a screenshot of a broken page.
"""
from __future__ import annotations

import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
IMG = ROOT / "docs" / "img"
# (page, output, width, full_page, run_the_example, scale)
# scale 1 on the full-page shot: index.html is ~14,000px tall and retina doubles
# that to a 6.6 MB file for no legibility gain at the width GitHub renders it.
# The audit page is shot at 2x because its numbers are the point.
SHOTS = [
    (ROOT / "index.html", IMG / "page-full.png", 1200, True, False, 1),
    (ROOT / "audit.html", IMG / "use-it.png", 1400, False, True, 2),
]


def shoot(page_path: Path, out: Path, width: int, full: bool, run_example: bool,
          scale: int = 2):
    if not page_path.exists():
        sys.exit(f"missing {page_path}")
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": width, "height": 1000},
                        device_scale_factor=scale)
        pg.goto(page_path.as_uri())
        if run_example:
            # Pyodide + the inlined package take a while on first load. Waiting
            # on the verdict rather than a fixed sleep means a slow machine
            # still gets a correct shot and a broken page still fails.
            pg.click("#tryexample")
            try:
                pg.wait_for_selector("#verdict", state="visible", timeout=120_000)
                pg.wait_for_function(
                    "document.querySelector('#verdict')"
                    "?.textContent.trim().length > 0", timeout=120_000)
            except Exception as e:
                b.close()
                sys.exit(f"FAILED: {page_path.name} never produced a verdict "
                         f"({type(e).__name__}). Not writing a screenshot of a "
                         f"page that does not work.")
            pg.wait_for_timeout(1200)   # let the rerank table paint
        else:
            pg.wait_for_load_state("networkidle")
            pg.wait_for_timeout(800)
        pg.screenshot(path=str(out), full_page=full)
        b.close()
    kb = out.stat().st_size // 1024
    print(f"  {out.relative_to(ROOT)}  {kb} KB")


if __name__ == "__main__":
    print("re-shooting the README images from the current pages")
    for args in SHOTS:
        shoot(*args)
    print("done")
