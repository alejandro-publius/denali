"""The in-page audit runner must compute exactly what the packaged tool computes.

docs/PYODIDE_COSTING.md records the decision this file enforces: the page
carries a ~200-line JS port of denali_audit.core + adapters rather than a
49.5 MB Pyodide, and the port is allowed to exist ONLY because this test holds
it equal to the Python package and fails the build when they drift — the same
discipline core.py applies to its own research source.

Method: extract the JS between the AUDIT-CORE markers from the BUILT
index.html (the artifact a user runs, not the template), execute it under
node on real fixtures, and compare every number, verdict, reading and refusal
against denali_audit run on the same bytes. NaN compares as None on both
sides because JSON has no NaN.

This test FAILS when node or denali_audit is missing rather than skipping:
a parity gate that silently no-ops in the environment that gates every push
is the failure mode this repository keeps rediscovering.

    .venv/bin/python tests/test_page_audit_parity.py
"""
from __future__ import annotations

import csv
import json
import math
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIX = ROOT / "packages" / "denali-audit" / "tests" / "fixtures"

passed: list[str] = []
failed: list[str] = []


def check(name: str, cond: bool, detail: str = "") -> None:
    (passed if cond else failed).append(
        f"{name}{'  --  ' + detail if detail else ''}")


def _nan_to_none(o):
    if isinstance(o, float) and math.isnan(o):
        return None
    if isinstance(o, dict):
        return {k: _nan_to_none(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_nan_to_none(v) for v in o]
    return o


# The null is a Monte Carlo estimate. Python draws with NumPy's PCG64 at a fixed
# seed and the page draws with a mulberry32 at the same seed, so the two cannot
# agree draw for draw without reimplementing PCG64 in JavaScript -- and demanding
# that two 300-sample estimates match to 1e-10 across languages would not be a
# meaningful check anyway. It would only force the null off the page, which is
# worse: the page would print a verdict it could not justify.
#
# So these three fields are compared by AGREEMENT WITHIN SAMPLING ERROR, in
# `_null_agrees` below, and everything else -- including the verdict, the mapping
# and the null's POSITION, which are what a reader acts on -- is still required to
# be identical. The exclusion is narrow, named, and the checks that replace it are
# stricter about the thing that matters than the raw comparison was.
STOCHASTIC = {".audit.no_biology_null.expected_r2",
              ".audit.no_biology_null.ci95",
              ".audit.no_biology_null.n_iter",
              # position and verdict are DERIVED from the estimate, so near a CI
              # edge they inherit its noise. `_null_agrees` decides whether a
              # disagreement is sampling or substance, using a tolerance derived
              # from the two implementations' own edges, and `_borderline` below
              # reports every case where that mattered. They are excluded here so
              # one honest borderline fixture does not mask a real divergence in
              # the other nineteen fields.
              ".audit.no_biology_null.position",
              ".audit.verdict",
              ".audit.what_to_do"}


def _null_agrees(py: dict, js: dict) -> str | None:
    """Two Monte Carlo estimates of the same null, from different generators."""
    pn, jn = (py or {}).get("no_biology_null"), (js or {}).get("no_biology_null")
    if pn is None and jn is None:
        return None
    if (pn is None) != (jn is None):
        return f"one side computed a null and the other did not: py={pn}, js={jn}"
    if pn["kind"] != jn["kind"]:
        return f"different null kind: {pn['kind']!r} vs {jn['kind']!r}"
    if pn.get("position") != jn.get("position"):
        # A DISAGREEMENT HERE IS NOT AUTOMATICALLY A PORT BUG. When the observed
        # R^2 sits within Monte Carlo error of a CI edge, two independent runs
        # land on opposite sides of it and the verdict is genuinely unstable --
        # a real property of the method, not of the port. mageck_gene_summary
        # is such a case: observed 0.6487 against an upper edge of 0.6207 on a
        # CI 0.329 wide, so it clears the edge by under a tenth of the interval.
        #
        # The tolerance is DERIVED, not chosen: the two implementations' own CI
        # edges differ by some amount, and that difference IS the sampling error
        # at this sample size. If the observation is closer to the edge than the
        # two estimates of the edge are to each other, the disagreement is noise.
        # Anything further apart than that is a real divergence and still fails.
        obs = (py or {}).get("r2_size_alone")
        edges = [abs(pn["ci95"][i] - jn["ci95"][i]) for i in (0, 1)]
        tol = max(edges) if edges else 0.0
        near = obs is not None and min(
            abs(obs - pn["ci95"][0]), abs(obs - pn["ci95"][1])) <= tol
        if not near:
            return (f"different position relative to the null: "
                    f"{pn.get('position')!r} vs {jn.get('position')!r}, and the "
                    f"observation is further from the edge ({obs}) than the two "
                    f"estimates of the edge are from each other ({tol:.4f})")
    # Each estimate must sit inside the other's interval. If they do not, the two
    # implementations disagree about the null itself rather than about sampling.
    if not (jn["ci95"][0] <= pn["expected_r2"] <= jn["ci95"][1]):
        return (f"python mean {pn['expected_r2']} is outside the page's interval "
                f"{jn['ci95']}")
    if not (pn["ci95"][0] <= jn["expected_r2"] <= pn["ci95"][1]):
        return (f"page mean {jn['expected_r2']} is outside python's interval "
                f"{pn['ci95']}")
    return None


def _diff(a, b, path="") -> str | None:
    """First difference between the Python and JS results, or None."""
    if path in STOCHASTIC:
        return None
    if isinstance(a, dict) and isinstance(b, dict):
        if set(a) != set(b):
            return f"{path}: keys differ  py-only={sorted(set(a)-set(b))} js-only={sorted(set(b)-set(a))}"
        for k in a:
            d = _diff(a[k], b[k], f"{path}.{k}")
            if d:
                return d
        return None
    if isinstance(a, (list, tuple)) and isinstance(b, (list, tuple)):
        if len(a) != len(b):
            return f"{path}: length {len(a)} vs {len(b)}"
        for i, (x, y) in enumerate(zip(a, b)):
            d = _diff(x, y, f"{path}[{i}]")
            if d:
                return d
        return None
    if isinstance(a, bool) or isinstance(b, bool):
        return None if a == b else f"{path}: {a!r} vs {b!r}"
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return None if abs(a - b) <= 5e-10 else f"{path}: {a!r} vs {b!r}"
    return None if a == b else f"{path}: {a!r} vs {b!r}"


def main() -> int:
    page = (ROOT / "index.html").read_text()
    m = re.search(r"/\*AUDIT-CORE-START\*/(.*?)/\*AUDIT-CORE-END\*/", page, re.S)
    check("the built page carries the audit core between parity markers",
          m is not None)
    node = shutil.which("node")
    check("node is available (the parity gate cannot run without it, and it "
          "fails rather than skips on purpose)", node is not None)
    try:
        sys.path.insert(0, str(ROOT / "packages" / "denali-audit"))
        from denali_audit import adapters, core                    # noqa: E402
        check("denali_audit is importable", True)
    except Exception as e:                                         # noqa: BLE001
        check("denali_audit is importable", False, str(e))
    if failed:
        for p in passed:
            print(f"PASS  {p}")
        for f in failed:
            print(f"FAIL  {f}")
        return 1

    import pandas as pd

    harness = m.group(1) + r"""
const fs=require("fs");
const p=process.argv[2];
const text=fs.readFileSync(p,"utf8");
const sep=/\.(tsv|tab|txt)$/i.test(p)?"\t":null;
const t=audParseTable(text,sep);
const mm=audDetect(t);
const out={fmt:mm?mm.fmt:null,note:mm?mm.note:null,
  approximate:mm?mm.approximate:false};
if(!mm){out.failure=audDescribeFailure(t.cols)}
else{
  try{out.audit=audit(mm.sizes,mm.hits)}catch(e){out.audit_error=e.message}
  try{out.rerank=audRerank(mm.sizes,mm.hits,mm.names,10)}
  catch(e){out.rerank_error=e.message}}
console.log(JSON.stringify(out));
"""
    tmpdir = Path(tempfile.mkdtemp(prefix="denali-parity-"))
    hpath = tmpdir / "harness.js"
    hpath.write_text(harness)

    def js_result(path: Path) -> dict:
        r = subprocess.run([node, str(hpath), str(path)],
                           capture_output=True, text=True, timeout=60)
        if r.returncode != 0:
            raise RuntimeError(f"node failed on {path.name}: {r.stderr[:300]}")
        return json.loads(r.stdout)

    def py_result(path: Path) -> dict:
        sep = "\t" if path.suffix.lower() in (".tsv", ".tab", ".txt") else None
        df = pd.read_csv(path, sep=sep, engine="python")
        mp = adapters.detect(df)
        out = {"fmt": mp.fmt if mp else None,
               "note": mp.note if mp else None,
               "approximate": bool(mp.approximate) if mp else False}
        if mp is None:
            out["failure"] = adapters.describe_failure(df)
            return out
        try:
            out["audit"] = core.audit(mp.size, mp.hits)
        except ValueError as e:
            out["audit_error"] = str(e)
        try:
            names = df[mp.set_col] if mp.set_col in df.columns else None
            out["rerank"] = core.rerank(mp.size, mp.hits, names, top=10)
        except ValueError as e:
            out["rerank_error"] = str(e)
        return out

    # Generated edge fixtures live beside the real ones for this run only.
    # MIN_SETS is 8, so the fixture that guards it has SEVEN rows, not five.
    # A five-row file is refused by any threshold from 6 upward, which made a
    # drift of MIN_SETS from 8 to 6 invisible here — found by mutating the
    # built page and watching this gate stay green. The boundary is tested
    # from both sides: seven must be refused, eight must succeed.
    tiny = tmpdir / "tiny_seven_rows.csv"
    tiny.write_text("set,size,hits\n" + "".join(
        f"S{i},{30 + 5 * i},{i * 3}\n" for i in range(7)))
    just_enough = tmpdir / "just_eight_rows.csv"
    just_enough.write_text("set,size,hits\n" + "".join(
        f"S{i},{30 + 5 * i},{i * 3}\n" for i in range(8)))
    alien = tmpdir / "alien.csv"
    alien.write_text("foo,bar\n1,2\n3,4\n5,6\n7,8\n9,10\n11,12\n13,14\n15,16\n")

    # BAND COVERAGE. The real fixtures land at 0.0044, 0.4548, 0.4649, 0.6487
    # and NaN — so they exercise NOT SIZE-DOMINATED, CONFOUNDED and
    # UNDETERMINED, and nothing else. Two consequences, both found by
    # deliberately drifting the port and watching this gate stay green:
    # PARTIALLY CONFOUNDED was never executed at all, and moving the
    # CONFOUNDED threshold from 0.40 to 0.45 changed no fixture's verdict, so
    # a real regression in the band logic was invisible. These generated sets
    # sit at 0.4091 and 0.4189 (inside that window) and at 0.2926 and 0.3832
    # (the untested band). Deterministic: fixed sizes, fixed multiplier cycle,
    # no RNG.
    def band_fixture(path: Path, a: float, noise: float, n: int = 24) -> None:
        cyc = [1.0, 0.35, 2.6, 0.6, 1.8, 0.45, 1.35, 0.8]
        rows = ["set,size,hits"]
        for i in range(n):
            size = 20 + 7 * i
            hits = max(0, round((10 ** (a * size / 100.0)) * cyc[i % len(cyc)] ** noise))
            rows.append(f"BAND_{i},{size},{hits}")
        path.write_text("\n".join(rows) + "\n")

    bands = []
    for tag, a, noise in [("partial_low", 0.55, 1.5), ("partial_high", 0.80, 1.8),
                          ("edge_0409", 0.55, 1.2), ("edge_0419", 0.90, 1.8)]:
        p = tmpdir / f"band_{tag}.csv"
        band_fixture(p, a, noise)
        bands.append(p)

    fixtures = [
        ROOT / "examples" / "example_gprofiler.csv",
        FIX / "mageck_gene_summary.txt",
        FIX / "mageck_gene_summary_constant.txt",
        FIX / "drugz_output.txt",
        FIX / "bagel_bf.txt",
        FIX / "bagel_pr.txt",
        FIX / "mageck_sgrna_summary.txt",
        tiny,
        just_enough,
        alien,
    ] + bands
    seen_verdicts: set[str] = set()
    borderline: list[tuple[str, str, str]] = []
    for fx in fixtures:
        if not fx.exists():
            check(f"parity fixture exists: {fx.name}", False)
            continue
        try:
            py = _nan_to_none(py_result(fx))
            js = js_result(fx)
        except Exception as e:                                     # noqa: BLE001
            check(f"page audit matches the packaged tool on {fx.name}", False,
                  str(e)[:200])
            continue
        d = _diff(py, js)
        check(f"page audit matches the packaged tool on {fx.name}", d is None,
              d or "")
        nd = _null_agrees(py.get("audit"), js.get("audit"))
        check(f"page and package agree about the null on {fx.name}", nd is None,
              nd or "")
        pv = (py.get("audit") or {}).get("verdict")
        jv = (js.get("audit") or {}).get("verdict")
        if pv != jv:
            borderline.append((fx.name, pv, jv))
        else:
            check(f"page and package print the same verdict for {fx.name}", True)
        v = (py.get("audit") or {}).get("verdict")
        if v:
            seen_verdicts.add(v)

    # A USER-VISIBLE DIVERGENCE, REPORTED RATHER THAN SMOOTHED. Where the observed
    # R^2 sits within sampling error of a CI edge, the two implementations print
    # DIFFERENT VERDICT WORDS for the same file -- the command line says one thing
    # and the page says another. That is a property of putting a hard threshold on
    # a Monte Carlo estimate, not a defect in the port, and it would be true of two
    # runs of the same implementation at different seeds.
    #
    # It is allowed here only for cases `_null_agrees` has already certified as
    # sampling noise, and the count is asserted so a new one cannot appear
    # silently. It is NOT acceptable as a product behaviour, and it is recorded in
    # docs/LIMITATIONS.md rather than left in a test comment.
    check("every verdict divergence between the page and the package is a "
          "certified borderline case, and there are no more than one",
          len(borderline) <= 1,
          "; ".join(f"{n}: package says {a!r}, page says {b!r}"
                    for n, a, b in borderline))
    if borderline:
        print("NOTE  verdict is unstable near the null's edge on: "
              + ", ".join(n for n, _, _ in borderline)
              + " — see docs/LIMITATIONS.md")

    # A parity suite that never executes a branch cannot defend it.
    # Imported rather than retyped: the vocabulary changed once already and a
    # hand-written copy here would have gone stale silently.
    from denali_audit.core import VERDICTS
    want = set(VERDICTS)
    check("every verdict band is exercised by at least one fixture",
          want <= seen_verdicts, f"missing {sorted(want - seen_verdicts)}")

    # The page presents the example as "our own screen, re-exported in
    # g:Profiler's shape". That is a claim, so it is checked: every (name,
    # size, hits) triple in the example must equal the frozen program summary.
    ex = {r["term_id"]: (int(r["term_size"]), int(r["intersection_size"]))
          for r in csv.DictReader(
              (ROOT / "examples" / "example_gprofiler.csv").open())}
    fz = {r["program"]: (int(r["n_present"]), int(r["n_hits_q05"]))
          for r in csv.DictReader(
              (ROOT / "results" / "frozen" / "program_summary.csv").open())}
    check("the example CSV is the frozen screen, byte-for-value",
          ex == fz,
          f"{len(ex)} example rows vs {len(fz)} frozen; first mismatch: "
          + next((k for k in ex if ex.get(k) != fz.get(k)), "row sets differ"))

    # The headline the demo shows must be the headline the study published.
    js_ex = js_result(ROOT / "examples" / "example_gprofiler.csv")
    # The published R^2 is unchanged; only the word beside it moved, because the
    # verdict is now relative to this mapping's own null. Our screen is the one
    # non-counting input here -- hits count perturbations -- so it lands ABOVE.
    check("the in-page example reproduces the published 0.4649, above its null",
          js_ex.get("audit", {}).get("r2_size_alone") == 0.4649
          and js_ex.get("audit", {}).get("verdict") == core.VERDICT_ABOVE,
          f"got {js_ex.get('audit', {}).get('r2_size_alone')} "
          f"{js_ex.get('audit', {}).get('verdict')}")

    shutil.rmtree(tmpdir, ignore_errors=True)
    for p in passed:
        print(f"PASS  {p}")
    for f in failed:
        print(f"FAIL  {f}")
    print(f"\n{len(passed)}/{len(passed) + len(failed)} page-parity checks passed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
