"""Does any rendered surface disagree with any other about the same number?

The main suite checks each surface against the frozen files. That catches a
surface drifting from the data. It does not catch two surfaces drifting from
each other in a place neither is individually asserted -- which is how this
project has repeatedly ended up with "ten evaluations" on one page and eleven on
another, and how a stale figure survives in a doc nobody thought to guard.

This asks a different question: for each named quantity, gather every value any
surface states for it, and fail if they are not all the same.

The design decision that matters is that a quantity is found by its SURROUNDING
PHRASE, not by its value. Searching for "0.751" only finds surfaces that already
agree; searching for "adj R²" and then reading the number next to it finds the
one that says 0.75.

    .venv/bin/python tests/test_cross_surface.py

Run by `make test` after the main suite. Adding a quantity is one row.
"""
from __future__ import annotations

import json
import re
import sys
import pathlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Every surface a reader can actually reach. Not src/ -- code comments are
# allowed to discuss superseded values, and the frozen JSON is the truth these
# are checked against elsewhere.
SURFACES = [
    "README.md", "REPORT.md", "index.html", "app.py",
    "docs/DEMO.md", "docs/SUBMISSION.md", "docs/DECK.md", "docs/LITERATURE.md",
    "docs/CORPUS.md", "docs/ADVERSARIAL.md", "docs/MORNING_HANDOFF.md",
    "docs/LIMITATIONS.md", "docs/LOOP.md", "docs/OFFTARGET.md",
    "results/figures/CAPTIONS.md", "results/corpus_rerank/README.md",
    # Added after both drifted unnoticed: SUBMISSION_IMPACTFORGE.md stated a
    # stale cross-surface count and stale dependency floors, and the package
    # README told readers to install from PyPI where nothing is published.
    # A prose surface nobody registered is a prose surface nobody checks.
    "docs/SUBMISSION_IMPACTFORGE.md", "packages/denali-audit/README.md",
]

# Any .md a reader can reach that states a headline number should be in
# SURFACES above. This catches the ones nobody remembered to add.
_UNREGISTERED_HINT = ("docs", "packages")

# label -> (context regex with ONE capture group, canonical value, equivalents)
# The regex must anchor on words, so a surface stating a WRONG value is found
# rather than skipped. `equivalents` lists spellings that mean the same number.
QUANTITIES = {
    "adj R2, all six features": (
        r"(?:adj(?:usted)?\.? R[²2][^.\n]{0,40}?|all six[^.\n]{0,30}?)\b(0\.7\d{1,3})\b",
        "0.751", {"0.7511", "0.751"}),
    "adj R2, outcome-independent five": (
        r"(?:0\.561|outcome-independent[^.\n]{0,40}?\b(0\.5\d{1,3})\b)",
        "0.561", {"0.561", "0.5606"}),
    "R2, set size alone": (
        r"(?:size alone|set size alone)[^.\n]{0,60}?\b(0\.4\d{1,3}|4\d(?:\.\d)?%)\b",
        "0.4649", {"0.4649", "0.465", "46.5%", "46%"}),
    "held-out balanced accuracy": (
        r"balanced accuracy[^.\n]{0,40}?\b(0\.\d{2,4})\b",
        "0.4375", {"0.4375"}),
    "guide-pair concordance": (
        r"concordance[^.\n]{0,40}?([−-]0\.0\d{1,3})\b",
        "-0.019", {"-0.019", "−0.019"}),
    "corpus median size-confound": (
        r"(?:field's median|median size-confound|median)[^.\n]{0,40}?\b(0\.2\d{1,3})\b",
        "0.224", {"0.224"}),
    # (?<![\d.]) or this matches the "4.4%" inside Tier B's "14.4%" -- the two
    # sit in the same sentence, which is exactly the trap a value-blind pattern
    # falls into.
    "literature Tier A share": (
        r"(?:Tier A|mention (?:gene-)?set size)[^.\n]{0,80}?(?<![\d.])(\d\.\d%)",
        "3.6%", {"3.6%"}),
    "literature Tier B share": (
        r"(?:Tier B|competitive-test machinery)[^.\n]{0,80}?(?<![\d.])(1\d\.\d%)",
        "14.4%", {"14.4%"}),
    "literature resolved count": (
        r"(?:resolved|open access)[^.\n]{0,60}?\b(1\d{2})\b",
        "111", {"111"}),
}


def _norm(v: str) -> str:
    return v.replace("−", "-").strip()


def main() -> int:
    texts = {}
    for s in SURFACES:
        p = ROOT / s
        if p.exists():
            texts[s] = p.read_text(errors="ignore")

    passed, failed = [], []

    def check(name, cond, detail=""):
        (passed if cond else failed).append(f"{name}{'  --  ' + detail if detail else ''}")

    for label, (pat, canon, equiv) in QUANTITIES.items():
        rx = re.compile(pat, re.I)
        seen = {}
        for s, t in texts.items():
            for m in rx.finditer(t):
                g = next((x for x in m.groups() if x), None)
                if g:
                    seen.setdefault(_norm(g), set()).add(s)
        if not seen:
            # A quantity nothing states is a stale row in this table, and that
            # is a defect in the guard rather than in the repo -- say so.
            check(f"cross-surface: {label} is stated somewhere", False,
                  "no surface matched the context pattern; the pattern is stale")
            continue
        bad = {v: ss for v, ss in seen.items() if v not in equiv}
        check(f"cross-surface: every surface agrees on {label}", not bad,
              f"canonical {canon}; found "
              + "; ".join(f"{v!r} in {sorted(x.split('/')[-1] for x in ss)}"
                          for v, ss in (bad or seen).items()))

    # Evaluation and negative counts, read from the README findings table --
    # the same single source of truth the main suite uses, checked here across
    # every surface that spells the number as a word.
    readme = texts.get("README.md", "")
    rows = re.findall(r"^\|\s*(\d+)\s*\|.*\|\s*\*\*([A-Z][A-Z ]+)\*\*", readme, re.M)
    n_eval = len(rows)
    n_neg = [v.strip() for _, v in rows].count("NEGATIVE")
    words = {1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six",
             7: "seven", 8: "eight", 9: "nine", 10: "ten", 11: "eleven",
             12: "twelve"}
    ev_w, neg_w = words.get(n_eval, ""), words.get(n_neg, "")
    wrong = {}
    for s, t in texts.items():
        for m in re.finditer(r"\b(\w+) of (\w+) evaluations\b", t, re.I):
            a, b = m.group(1).lower(), m.group(2).lower()
            if (a, b) != (neg_w, ev_w):
                wrong.setdefault(f"{a} of {b}", set()).add(s)
        for m in re.finditer(r"\b(\w+) evaluations\b", t, re.I):
            a = m.group(1).lower()
            if a in words.values() and a != ev_w:
                wrong.setdefault(f"{a} evaluations", set()).add(s)
    check(f"cross-surface: every surface says {neg_w} of {ev_w} evaluations",
          not wrong,
          "; ".join(f"{k!r} in {sorted(x.split('/')[-1] for x in v)}"
                    for k, v in wrong.items()))

    # A claim of the form "git diff X..HEAD matches nothing under src/" is
    # checkable, and three of them shipped returning the opposite of the
    # sentence beside them. Any surface that argues from a commit range must
    # have that argument still be true, or not make it.
    import subprocess
    for s, txt in texts.items():
        for m in re.finditer(
                r"`git diff --name-only ([0-9a-f]{7,40})\.\.HEAD`[^.]{0,120}?"
                r"matches nothing under `src/`", txt):
            sha = m.group(1)
            try:
                out = subprocess.run(
                    ["git", "diff", "--name-only", f"{sha}..HEAD", "--", "src", "Makefile"],
                    cwd=ROOT, capture_output=True, text=True, timeout=30).stdout.strip()
            except Exception as e:                       # noqa: BLE001
                out = f"(could not run: {e})"
            check(f"cross-surface: {s} 'nothing under src/' since {sha} is still true",
                  out == "",
                  f"git says: {out.replace(chr(10), ', ') or '(empty)'}")
        # Same shape, counted rather than listed. Skip text inside *italics* or
        # "quotes": the README explains this failure mode by quoting the bad
        # sentence, and a guard that cannot tell a cautionary example from a
        # live claim would make documenting the lesson impossible.
        for m in re.finditer(r"[Tt]he (one|two|three|four|five) commits? after it", txt):
            ctx = txt[max(0, m.start() - 60):m.start()]
            if ctx.rstrip().endswith(('*"', '"', '*', "'")) or '*"' in ctx[-30:]:
                continue
            check(f"cross-surface: {s} does not count commits that had not been written",
                  False,
                  f"{m.group(0)!r} -- a commit count after a named SHA goes stale "
                  "the moment anyone pushes; name the commit and let the reader re-run")

    # A markdown table with a blank line in it silently becomes literal pipe
    # text. The findings table -- the single source of truth this whole suite
    # parses -- shipped with five blank lines in it and a paragraph splitting
    # rows 9 and 10, so seven of eleven rows did not render on GitHub at all.
    # The parser that reads it does not care about blank lines; a reader does.
    for s, txt in texts.items():
        if not s.endswith(".md"):
            continue
        block, blank_in_table, para_in_table = [], 0, 0
        prev_pipe = False
        for i, ln in enumerate(txt.split("\n")):
            is_pipe = ln.startswith("|")
            if prev_pipe and not is_pipe and ln.strip():
                # a non-blank non-pipe line directly after a row: fine only if
                # the table has ended (no pipe row follows within 2 lines)
                nxt = txt.split("\n")[i + 1:i + 3]
                if any(x.startswith("|") for x in nxt):
                    para_in_table += 1
            if prev_pipe and not ln.strip():
                nxt = txt.split("\n")[i + 1:i + 2]
                if nxt and nxt[0].startswith("|"):
                    blank_in_table += 1
            prev_pipe = is_pipe
        check(f"cross-surface: no markdown table in {s} is broken by a blank line "
              "or a paragraph",
              blank_in_table == 0 and para_in_table == 0,
              f"{blank_in_table} blank line(s) and {para_in_table} paragraph(s) "
              "inside a table -- those rows render as literal pipes")

    # The rerank table in the README is the project's single strongest
    # demonstration -- our own number one falling twenty-three places -- and it
    # is 35 hand-typed cells. Re-derive it from the packaged tool rather than
    # trusting that it was right the day it was pasted in.
    readme_md = texts.get("README.md", "")
    if "## What the tool does to our own result" in readme_md:
        import subprocess, tempfile, csv as _csv
        sec = readme_md.split("## What the tool does to our own result", 1)[1]
        rows = re.findall(
            r"^\| `(HALLMARK_\w+)` \| ([\d,]+) \| ([\d,]+) \| \*{0,2}(\d+) → (\d+)\*{0,2} \| −(\d+) \|",
            sec, re.M)
        import shutil
        # PATH first so CI (system python) finds it, venv second for local use.
        # NOT an optional skip: CI installs the package precisely so this runs,
        # and a guard that quietly no-ops in the one environment that gates
        # every push is the failure mode this repo keeps rediscovering.
        venv = pathlib.Path(shutil.which("denali") or (ROOT / ".venv" / "bin" / "denali"))
        summ = ROOT / "results" / "frozen" / "program_summary.csv"
        if not rows:
            check("cross-surface: the README rerank table is parseable", False,
                  "no rows matched -- the table changed shape or vanished")
        elif not venv.exists():
            check("cross-surface: the README rerank table matches the tool", False,
                  "denali is not installed, so this check cannot run. "
                  "`pip install -e packages/denali-audit`. It fails rather than "
                  "skipping on purpose.")
        else:
            with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False,
                                             newline="") as fh:
                w = _csv.writer(fh); w.writerow(["set", "size", "hits"])
                with open(summ, newline="") as src:
                    for r in _csv.DictReader(src):
                        w.writerow([r["program"], r["n_present"], r["n_hits_q05"]])
                tmp = fh.name
            out = subprocess.run([str(venv), "rerank", tmp, "--top", "10"],
                                 capture_output=True, text=True, timeout=120).stdout
            live = {m.group(1): (int(m.group(2)), int(m.group(3)), int(m.group(4)),
                                 int(m.group(5)), int(m.group(6)))
                    for m in re.finditer(
                        r"(HALLMARK_\w+)\s+(\d+)\s+(\d+)\s+(\d+) -> (\d+)\s+\((-\d+)\)", out)}
            bad = []
            for name, size, hits, r1, r2, d in rows:
                want = (int(size.replace(",", "")), int(hits.replace(",", "")),
                        int(r1), int(r2), -int(d))
                if live.get(name) != want:
                    bad.append(f"{name}: README {want} vs tool {live.get(name)}")
            check("cross-surface: every cell of the README rerank table matches "
                  "the packaged tool",
                  not bad and len(rows) == len(live),
                  "; ".join(bad[:3]) if bad
                  else f"{len(rows)} rows x 5 cells re-derived from `denali rerank`")

    # ---- the web surface must be the package, not a copy of it ------------
    # audit.html runs denali_audit in the browser by carrying its source inline.
    # That is the only way the page can claim to be "the same code"; it is also
    # a second copy, and a second copy goes stale. The builder is re-run here and
    # the committed page must match it byte for byte.
    page = ROOT / "audit.html"
    if page.exists():
        sys.path.insert(0, str(ROOT / "web"))
        import build_audit_page
        check("cross-surface: audit.html carries the CURRENT package source",
              build_audit_page.build() == page.read_text(),
              "stale — run: python3 web/build_audit_page.py")
        inlined = json.loads(re.search(
            r'<script id="denali-src" type="application/json">(.*?)</script>',
            page.read_text(), re.S).group(1).replace("<\\/", "</"))
        pkg = ROOT / "packages" / "denali-audit" / "denali_audit"
        drift = [n for n, src in inlined.items() if (pkg / n).read_text() != src]
        check("cross-surface: every module inlined in audit.html is byte-identical "
              "to the packaged one", not drift, ", ".join(drift))

        # The inlined MODULES are byte-checked above. The page's own driver --
        # the ~50 lines of Python the page wraps around them -- is not a module
        # and was checked by nothing, so a NameError in it shipped green and
        # only appeared when a browser ran it. Execute it here against the real
        # package and require it to agree with the package's own functions.
        drv = re.search(r"var DRIVER = \[(.*?)\]\.join\(\"\\n\"\);",
                        page.read_text(), re.S)
        check("cross-surface: audit.html carries an extractable Python driver",
              drv is not None)
        if drv:
            import io as _io
            import pandas as _pd
            sys.path.insert(0, str(pkg.parent))
            ns: dict = {}
            try:
                exec(compile("\n".join(json.loads("[" + drv.group(1) + "]")),
                             "<audit.html driver>", "exec"), ns)
                err = None
            except Exception as e:                              # noqa: BLE001
                err = f"{type(e).__name__}: {e}"
            check("cross-surface: the page's Python driver imports and compiles",
                  err is None, err or "")
            if err is None:
                ex = (ROOT / "examples" / "example_gprofiler.csv")
                got = json.loads(ns["run"](ex.read_text(), ex.name))
                from denali_audit.core import audit as _pkg_audit
                from denali_audit.adapters import detect as _pkg_detect
                _df = _pd.read_csv(_io.StringIO(ex.read_text()))
                _m = _pkg_detect(_df)
                want = _pkg_audit(_m.size, _m.hits)
                check("cross-surface: the page's driver returns the package's "
                      "own audit numbers",
                      got.get("ok") and got["audit"]["r2_size_alone"]
                      == want["r2_size_alone"]
                      and got["audit"]["verdict"] == want["verdict"],
                      f"page {got.get('audit', {}).get('r2_size_alone')} vs "
                      f"package {want['r2_size_alone']}")
                # Every metric the page offers must be one the package accepts,
                # or the dropdown hands the user a refusal.
                from denali_audit.core import BASELINE_METRICS as _BM
                check("cross-surface: every metric the page offers is one the "
                      "package implements",
                      sorted(got.get("metrics", [])) == sorted(_BM),
                      f"page {sorted(got.get('metrics', []))} vs "
                      f"package {sorted(_BM)}")
                # The baseline route, end to end through the page's own driver.
                _b = json.loads(ns["run_baseline"](
                    ex.read_text(), ex.name, "query_size", "spearman", 10))
                check("cross-surface: the page's baseline driver refuses a "
                      "constant prediction column rather than scoring it",
                      _b.get("ok") is True
                      and _b["baseline"].get("your_score") is None,
                      str(_b)[:120])
                _bad = json.loads(ns["run_baseline"](
                    ex.read_text(), ex.name, "intersection_size", "auroc", 10))
                check("cross-surface: the page's baseline driver refuses a "
                      "metric the package does not know",
                      _bad.get("ok") is False
                      and "unrecognised metric" in _bad.get("message", ""),
                      str(_bad)[:120])
                # The atlas lookup, through the page, must return the package's
                # own number -- and must refuse rather than invent one for a
                # screen it does not carry.
                from denali_audit.atlas import FLOORS, N_SCREENS
                from denali_audit.atlas import floor as _pkg_floor
                _sid = sorted(FLOORS)[0]
                _pf = json.loads(ns["run_floor"](str(_sid)))
                check("cross-surface: the page's atlas lookup returns the "
                      "package's own floor",
                      _pf.get("no_biology_floor")
                      == _pkg_floor(_sid)["no_biology_floor"],
                      f"page {_pf.get('no_biology_floor')} vs package "
                      f"{_pkg_floor(_sid)['no_biology_floor']}")
                check("cross-surface: the page's atlas lookup refuses a screen "
                      "it does not carry rather than inventing a floor",
                      json.loads(ns["run_floor"]("999999")).get("status")
                      == "NOT_IN_ATLAS"
                      and json.loads(ns["run_floor"]("zzz")).get("status")
                      == "NOT_IN_ATLAS")
                # The page states the atlas size in prose. It is injected from
                # the package at build time, so it cannot be stale -- but only
                # if nobody types it back in, which is what this catches.
                check("cross-surface: the atlas size stated on the page is the "
                      "size the shipped atlas actually has",
                      f"<b>{N_SCREENS:,}</b>" in page.read_text(),
                      f"page does not state {N_SCREENS:,}")

    # Two surfaces state how many files are in docs/, and both were stale: the
    # index said 33 and the README said twenty-seven while there were 40. A
    # count of files on disk is the cheapest possible thing to derive and it had
    # drifted by thirteen, which is what makes it worth a guard rather than
    # another correction. Spelled digits and words both, because the README used
    # a word and the index used a numeral.
    _ndocs = len(list((ROOT / "docs").glob("*.md")))
    _words = {27: "twenty-seven", 33: "thirty-three", 43: "forty-three"}
    for _s, _pat in (("docs/README.md", r"^(\d+) files is a lot to land in"),
                     ("README.md",
                      r"documentation index\*\* — (\d+|[a-z-]+) files")):
        _t = texts.get(_s, (ROOT / _s).read_text() if (ROOT / _s).exists() else "")
        _m = re.search(_pat, _t, re.M)
        _said = _m.group(1) if _m else None
        check(f"cross-surface: {_s} states the real number of docs",
              _said in (str(_ndocs), _words.get(_ndocs)),
              f"says {_said!r}, docs/ has {_ndocs} .md files")

    # ---- the atlas must not drift from the corpus it summarises ------------
    # Same discipline as audit.html: the generated module is regenerated here
    # and the committed one must match, so a corpus edit that never reaches the
    # shipped atlas is a red build rather than a citation that means two things.
    atlas_py = ROOT / "packages" / "denali-audit" / "denali_audit" / "atlas.py"
    if atlas_py.exists():
        sys.path.insert(0, str(ROOT))
        import importlib
        _ba = importlib.import_module("src.build_atlas")
        check("cross-surface: atlas.py carries the CURRENT corpus",
              _ba.build() == atlas_py.read_text(),
              "stale — run: .venv/bin/python -m src.build_atlas")
        import hashlib as _hl
        _csv = ROOT / "results" / "corpus" / "corpus_per_screen.csv"
        _want = _hl.sha256(_csv.read_bytes()).hexdigest()
        check("cross-surface: the hash the atlas tells people to cite is the "
              "hash of the table it came from",
              f'SOURCE_SHA256 = {_want!r}' in atlas_py.read_text(),
              f"expected {_want[:16]}")

    for p in passed:
        print(f"PASS  {p}")
    for f in failed:
        print(f"FAIL  {f}")
    print(f"\n{len(passed)}/{len(passed) + len(failed)} cross-surface checks passed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
