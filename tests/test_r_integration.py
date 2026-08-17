"""The R entry point must return the packaged tool's numbers, not its own.

`integrations/denali.R` exists so an R user running clusterProfiler can audit a
ranking in the ten seconds after it appears rather than a week later, which is
the only moment the check changes a decision. It is a thin shell over the CLI
for exactly one reason: core.py's docstring says the maths must not drift, and
an R reimplementation is the drift it warns about.

That argument is only worth anything if something checks it. This runs the R
file and the Python package over the same bytes and fails the build if any
value differs -- the same discipline `tests/test_page_audit_parity.py` applies
to the browser port.

WHY THE FIXTURE IS SYNTHETIC. clusterProfiler is not installed here (it is a
heavy Bioconductor dependency and `make all` must not need it). The contract
between the two projects is not the library, it is the SHAPE of what
`as.data.frame(enrichGO(...))` returns -- ID, Description, GeneRatio, BgRatio,
pvalue, p.adjust, qvalue, geneID, Count -- and the fixture is that shape
exactly. If clusterProfiler ever changes those column names this test keeps
passing while the integration breaks, so the shape is asserted explicitly below
rather than assumed.

Skips cleanly and loudly when R is absent. R is not needed to reproduce the
study and its absence must not fail the build.

    .venv/bin/python tests/test_r_integration.py
"""
from __future__ import annotations

import csv
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RFILE = ROOT / "integrations" / "denali.R"

passed: list[str] = []
failed: list[str] = []


def check(name: str, cond: bool, detail: str = "") -> None:
    (passed if cond else failed).append(
        f"{name}{'  --  ' + detail if detail else ''}")


# The columns clusterProfiler's enrichResult actually carries. Named here so a
# rename upstream is a visible edit to this list rather than a silent pass.
CLUSTERPROFILER_COLUMNS = ["ID", "Description", "GeneRatio", "BgRatio",
                           "pvalue", "p.adjust", "qvalue", "geneID", "Count"]


def fixture(path: Path) -> list[dict]:
    """A size-driven enrichment result in clusterProfiler's exact shape."""
    rows = []
    for i in range(30):
        bg = 20 + 13 * i
        cnt = max(1, round(bg * 0.06) + (i % 5) - 2)
        rows.append({
            "ID": f"GO:{i:07d}", "Description": f"biological process {i}",
            "GeneRatio": f"{cnt}/300", "BgRatio": f"{bg}/18000",
            "pvalue": 0.01, "p.adjust": 0.05, "qvalue": 0.05,
            "geneID": "GENEA/GENEB", "Count": cnt})
    with path.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=CLUSTERPROFILER_COLUMNS)
        w.writeheader()
        w.writerows(rows)
    return rows


def main() -> int:
    rscript = shutil.which("Rscript")
    if rscript is None:
        print("SKIP  Rscript is not installed. The study reproduces without R; "
              "install R to run this parity check.")
        return 0
    check("integrations/denali.R exists", RFILE.exists())
    if not RFILE.exists():
        print(f"FAIL  {failed[0]}")
        return 1

    sys.path.insert(0, str(ROOT / "packages" / "denali-audit"))
    try:
        import pandas as pd
        from denali_audit import adapters, core
    except Exception as e:                                       # noqa: BLE001
        print(f"FAIL  denali_audit is importable  --  {e}")
        return 1

    denali = ROOT / ".venv" / "bin" / "denali"
    if not denali.exists():
        d = shutil.which("denali")
        if d is None:
            print("FAIL  the denali CLI is not installed, so the R entry point "
                  "cannot be exercised. `pip install -e packages/denali-audit`. "
                  "This fails rather than skipping on purpose.")
            return 1
        denali = Path(d)

    tmp = Path(tempfile.mkdtemp(prefix="denali-r-"))
    csv_path = tmp / "cp_result.csv"
    fixture(csv_path)

    # 1. the adapter really does read clusterProfiler's shape unaided
    df = pd.read_csv(csv_path)
    check("the fixture carries clusterProfiler's own column names",
          list(df.columns) == CLUSTERPROFILER_COLUMNS, str(list(df.columns)))
    m = adapters.detect(df)
    check("denali recognises a clusterProfiler table with no flags",
          m is not None and m.fmt == "clusterProfiler",
          m.fmt if m else "not detected")

    script = f'''
source({str(RFILE)!r})
df <- read.csv({str(csv_path)!r})
a <- denali_audit(df, denali = {str(denali)!r})
r <- denali_rerank(df, top = 5, denali = {str(denali)!r})
cat(jsonlite::toJSON(list(audit = a, rerank = r), auto_unbox = TRUE, null = "null"))
'''
    proc = subprocess.run([rscript, "-e", script], capture_output=True,
                          text=True, timeout=300)
    check("the R entry point runs without error",
          proc.returncode == 0, (proc.stderr or "")[-300:])
    if proc.returncode != 0:
        for p in passed:
            print(f"PASS  {p}")
        for f in failed:
            print(f"FAIL  {f}")
        return 1

    got = json.loads(proc.stdout)
    want_a = core.audit(m.size, m.hits)
    want_r = core.rerank(m.size, m.hits, df[m.set_col], top=5)

    for key in ("verdict", "r2_size_alone", "n_sets", "spearman_size_vs_hits",
                "corpus_percentile"):
        check(f"R and the package agree on audit.{key}",
              got["audit"].get(key) == want_a.get(key),
              f"R {got['audit'].get(key)!r} vs package {want_a.get(key)!r}")
    for key in ("survived_top_n", "left_top_n", "biggest_fall", "top_n"):
        check(f"R and the package agree on rerank.{key}",
              got["rerank"].get(key) == want_r.get(key),
              f"R {got['rerank'].get(key)!r} vs package {want_r.get(key)!r}")

    # The refusal must survive the round trip. An integration that turns a
    # stated refusal into an empty result is worse than no integration.
    check("the R entry point carries what_this_is_not through to R",
          "not a candidate list" in
          str(got["rerank"].get("what_this_is_not", "")).lower(),
          str(got["rerank"].get("what_this_is_not"))[:60])

    # A missing CLI must say so in a sentence, not fail with an empty parse.
    bad = subprocess.run(
        [rscript, "-e", f'source({str(RFILE)!r}); '
                        f'denali_audit(read.csv({str(csv_path)!r}), '
                        f'denali = "definitely-not-installed-xyz")'],
        capture_output=True, text=True, timeout=120)
    check("a missing CLI produces an explanation, not an empty result",
          bad.returncode != 0 and "pip install" in bad.stderr,
          (bad.stderr or "")[-160:])

    # baseline must refuse to guess the metric through R too, or the R surface
    # is more permissive than every other surface.
    nom = subprocess.run(
        [rscript, "-e", f'source({str(RFILE)!r}); '
                        f'denali_baseline(read.csv({str(csv_path)!r}))'],
        capture_output=True, text=True, timeout=120)
    check("denali_baseline refuses to guess the metric from R",
          nom.returncode != 0 and "Neither is guessed" in nom.stderr,
          (nom.stderr or "")[-160:])

    shutil.rmtree(tmp, ignore_errors=True)
    for p in passed:
        print(f"PASS  {p}")
    for f in failed:
        print(f"FAIL  {f}")
    print(f"\n{len(passed)}/{len(passed) + len(failed)} R integration checks passed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
