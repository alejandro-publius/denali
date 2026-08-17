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
# THE IMPORT CLOSURE OF WHAT THE PAGE ACTUALLY RUNS, computed rather than listed.
#
# It was a hand-written tuple of four, and when core.py grew `from . import
# nulls` the page shipped a denali_audit missing it and died on the first click
# with a circular-import ImportError, for every visitor, while every guard stayed
# green -- the drift check compared the modules that WERE inlined against the
# package and had nothing to say about one that was not.
#
# The first fix was to inline every .py in the package. That removed the
# staleness but pulled in cli.py and verify.py, which the page never calls: it
# made the browser surface break whenever the command line changed, and grew the
# page by a fifth for code no visitor runs. So the rule is now the closure of
# what the page imports -- start at __init__ and the driver's own imports, follow
# `from . import x` and `from .x import ...` until it stops growing.
#
# Both failure modes are guarded in tests/test_cross_surface.py: the page must
# inline everything its closure needs, and that set must import itself in
# isolation. A module the page does not need is simply not carried.
def _closure() -> tuple[str, ...]:
    import re as _re
    pkg = (pathlib.Path(__file__).resolve().parent.parent /
           "packages" / "denali-audit" / "denali_audit")
    # Seeds: the package init, plus every module the page's own driver imports.
    tpl = (pathlib.Path(__file__).resolve().parent / "audit.template.html").read_text()
    seeds = {"__init__.py"}
    for mod in _re.findall(r"from denali_audit\.(\w+) import", tpl):
        seeds.add(mod + ".py")
    seen: set[str] = set()
    todo = list(seeds)
    while todo:
        name = todo.pop()
        if name in seen or not (pkg / name).exists():
            continue
        seen.add(name)
        src = (pkg / name).read_text()
        for dep in _re.findall(r"^\s*from \.(\w+) import", src, _re.M):
            todo.append(dep + ".py")
        for dep in _re.findall(r"^\s*from \. import (\w+)", src, _re.M):
            todo.append(dep + ".py")
    return tuple(sorted(seen))


MODULES = _closure()


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
