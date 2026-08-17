"""Build screen.html — the companion a scientist opens at stage 1, not stage 10.

WHY THERE IS A SECOND PAGE. audit.html does one thing: you have a results table,
it tells you how much of the ranking is set construction. That is stage 10 of
eleven, and by stage 10 the library is bought, the cells are transduced and the
sequencing is paid for. Everything that decides whether the screen can work has
already happened. This page is the same project arriving early enough to matter.

WHAT IS INJECTED RATHER THAN TYPED. The stage content and the corpus reference
classes both come from `web/screen_data.py`, which computes the reference classes
from `results/corpus/corpus_per_screen.csv` at build time. No number in the
rendered page is hand-written, and `tests/test_cross_surface.py` rebuilds this
file and fails if the committed one differs -- the same discipline audit.html is
held to.

    .venv/bin/python -m web.build_screen_page [--check]
"""
from __future__ import annotations

import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import screen_data  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "screen.html"
TEMPLATE = ROOT / "web" / "screen.template.html"

PLACEHOLDERS = ("__STAGES__", "__TOOLS__", "__REFERENCE__")


def build() -> str:
    t = TEMPLATE.read_text()
    for p in PLACEHOLDERS:
        if p not in t:
            raise SystemExit(f"template lost its {p} placeholder")
    blobs = {
        "__STAGES__": json.dumps(screen_data.STAGES, indent=1),
        "__TOOLS__": json.dumps(screen_data.TOOLS, indent=1),
        "__REFERENCE__": json.dumps(screen_data.reference_classes(), indent=1),
    }
    for k, v in blobs.items():
        # "</" escaped so a string containing </script> cannot close its own tag.
        t = t.replace(k, v.replace("</", "<\\/"))
    return t


def main() -> int:
    new = build()
    changed = (not OUT.exists()) or OUT.read_text() != new
    if "--check" in sys.argv:
        if changed:
            print("screen.html is STALE — run: "
                  ".venv/bin/python -m web.build_screen_page")
            return 1
        print("screen.html matches web/screen_data.py")
        return 0
    OUT.write_text(new)
    print(f"wrote {OUT.relative_to(ROOT)}  ({len(new)/1024:.0f} KB)"
          + ("" if changed else "  (unchanged)"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
