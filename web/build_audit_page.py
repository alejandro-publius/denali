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
MODULES = ("__init__.py", "core.py", "reference.py", "adapters.py")


def build() -> str:
    sources = {name: (PKG / name).read_text() for name in MODULES}
    # JSON escaping handles quotes and newlines; "</" is escaped separately so a
    # string containing </script> cannot close the tag it lives in.
    blob = json.dumps(sources, indent=1).replace("</", "<\\/")
    template = (ROOT / "web" / "audit.template.html").read_text()
    if "__DENALI_SOURCES__" not in template:
        raise SystemExit("template lost its __DENALI_SOURCES__ placeholder")
    return template.replace("__DENALI_SOURCES__", blob)


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
