"""Build audit.html by inlining the package's own source into the template.

WHY INLINE THE SOURCE rather than ship a wheel. The page runs the real
`denali_audit`, not a JavaScript restatement of it. core.py's own docstring says
the maths must not drift, and a browser reimplementation is exactly the drift it
warns about -- the study's credibility rests on the tool being the study's code.
So the four modules are pasted into the page verbatim and executed by CPython in
WebAssembly. A wheel would work too, and would add a build artifact to keep in
sync; the source is 42 KB and cannot go stale.

`tests/test_cross_surface.py` re-runs this builder and fails if the committed
audit.html differs, so an edit to the package that never reaches the page is a
red build rather than a silent divergence.

    python3 web/build_audit_page.py
"""
from __future__ import annotations

import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
PKG = ROOT / "packages" / "denali-audit" / "denali_audit"
# EVERY .py IN THE PACKAGE, discovered rather than listed. It was a hand-written
# tuple, and when core.py grew `from . import nulls` the page shipped a
# denali_audit missing nulls.py -- so audit.html died with a circular-import
# ImportError on the first click, for every visitor, while every guard stayed
# green. The drift check compares the modules that ARE inlined against the
# package and had nothing to say about one that was not, which is a check
# written in only one direction.
#
# Discovering the list removes the failure mode instead of correcting it, and
# tests/test_cross_surface.py now asserts the converse too.
MODULES = tuple(sorted(p.name for p in
                       (pathlib.Path(__file__).resolve().parent.parent /
                        "packages" / "denali-audit" / "denali_audit").glob("*.py")))


def build() -> str:
    sources = {name: (PKG / name).read_text() for name in MODULES}
    # JSON escaping handles quotes and newlines; "</" is escaped separately so a
    # string containing </script> cannot close the tag it lives in.
    blob = json.dumps(sources, indent=1).replace("</", "<\\/")
    template = (ROOT / "web" / "audit.template.html").read_text()
    if "__DENALI_SOURCES__" not in template:
        raise SystemExit("template lost its __DENALI_SOURCES__ placeholder")
    # The atlas size is READ FROM THE PACKAGE, never typed into the page. It is
    # the one number in this template's prose, and a page that states a screen
    # count the shipped atlas does not have is the drift this repo exists to
    # stop -- the same rule index.html follows for every frozen value.
    import re as _re
    n = int(_re.search(r"^N_SCREENS = (\d+)$",
                       sources["atlas.py"], _re.M).group(1))
    if "__ATLAS_N__" not in template:
        raise SystemExit("template lost its __ATLAS_N__ placeholder")
    return (template.replace("__DENALI_SOURCES__", blob)
                    .replace("__ATLAS_N__", f"{n:,}"))


def main() -> int:
    out = ROOT / "audit.html"
    new = build()
    changed = (not out.exists()) or out.read_text() != new
    if "--check" in sys.argv:
        if changed:
            print("audit.html is STALE — run: python3 web/build_audit_page.py")
            return 1
        print("audit.html matches the package source")
        return 0
    out.write_text(new)
    print(f"wrote {out.relative_to(ROOT)}  ({len(new)/1024:.0f} KB)"
          + ("" if changed else "  (unchanged)"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
