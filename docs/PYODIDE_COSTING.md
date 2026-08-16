# Pyodide, costed before building the in-page audit — decision record

2026-08-16. The Phase 4 brief was explicit: before adding any upload path to
`index.html`, cost out Pyodide — it would run `denali-audit` itself in the
browser and preserve the zero-network property. Costed here, with measured
numbers, before any build. **Decision: no Pyodide. The audit math is ported to
~200 lines of dependency-free JS inside the page, held equal to the Python
package by a build-failing test.**

## The measured cost

Sizes read from the CDN on 2026-08-16 (`curl -sIL`, content-length,
cdn.jsdelivr.net/pyodide/v0.26.2):

| asset | bytes |
|---|---:|
| pyodide.js + pyodide.asm.js | 1,244,395 |
| pyodide.asm.wasm | 10,087,885 |
| python_stdlib.zip + lock | 2,447,741 |
| numpy wheel (needed by core.py) | 11,959,233 |
| pandas wheel (needed by core.py + adapters.py) | 23,759,070 |
| **total to run the package verbatim** | **≈ 49.5 MB** |

Against the page's own published slow-3G benchmark (400 kbps, DESIGN.md "as a
judge meets it"): ≈ 17 minutes before the first verdict. The current page
paints its hero in 1.79 s.

## Why the cost cannot even be paid

It is not merely large — both ways of paying it are closed by the invariants
in `tests/test_frozen_invariants.py`:

- **From a CDN:** the suite fails the build on `<script src=` and on remote
  assets. Deliberately: the page must not be able to fail in front of a judge
  on venue wifi.
- **Inlined:** the suite greps the page for the literal `fetch(` — and
  `pyodide.asm.js` calls `fetch(` internally to load its own wasm and wheels.
  A byte-inlined Pyodide fails the no-network scan on its own source text,
  and 49.5 MB of base64 (≈ 66 MB encoded) in a file whose whole design is
  "complete at 1.1 MB" would be the end of the single-file property anyway.

A separate surface (a `try.html` that loads Pyodide from a CDN) was allowed by
the brief as a fallback. Rejected too: it recreates exactly the artifact this
project refuses — a demo that can fail unattended, on the network, in front of
an audience — to avoid a port of one OLS regression.

## What the math actually is

The size of the thing being ported decides this. `denali_audit.core` is, in
full: `log10`, a degree-1 `polyfit` (closed-form OLS), an R², a Spearman ρ
(average-rank transform + Pearson), stable argsort ranks, and a bisect into a
sorted list of 1,272 floats (`reference.py`, ~10 KB as JS data). No SciPy, no
linear algebra beyond a straight line. numpy and pandas — 35.7 of the 49.5 MB
— are imported for conveniences JS replicates in a few lines each.

## The drift risk, and the gate that closes it

The honest objection to a port: core.py is vendored verbatim from the research
code precisely so there is ONE implementation, and a JS copy is a second one.
The mitigation is the same one the package itself uses against its research
source: **an equality test that fails the build.**
`tests/test_page_audit_parity.py` extracts the audit JS from the built
`index.html`, runs it under `node` on `examples/example_gprofiler.csv` plus
edge fixtures (constant size, < 8 sets, zero-hit rows), and compares every
number and verdict against `denali_audit` run on the same input — to the same
4-decimal rounding the package itself applies. If the port drifts, the build
fails; if node is absent, the test fails loudly rather than skipping silently.

The corpus is not retyped either: the build reads `reference.py` and embeds
the same 1,272 values it finds there, so the reference distribution has one
source file in the repo, same as every number on the page.
