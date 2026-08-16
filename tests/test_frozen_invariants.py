"""Invariants over results/frozen/. Not biology — these lock the facts every
claim in this repository rests on, so a silent change fails loudly instead of
producing a confidently wrong page.

    .venv/bin/python tests/test_frozen_invariants.py     # or: make test

Three classes of check:
  A  the frozen numbers are what we say they are
  B  every headline number in REPORT.md and the page traces to a frozen file
  C  the scope rule -- no novel gene named -- enforced by scanning the rendered
     text rather than trusted to memory
"""
from __future__ import annotations

import ast
import json
import re
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
FROZEN = ROOT / "results" / "frozen"
FIGS = ROOT / "results" / "figures"
PASS: list[str] = []
FAIL: list[str] = []


def check(name: str, cond: bool, detail: str = "") -> None:
    (PASS if cond else FAIL).append(f"{name}{'  --  ' + detail if detail else ''}")


def near(a: float, b: float, tol: float = 5e-4) -> bool:
    return abs(float(a) - float(b)) <= tol


def _raises(fn, *args) -> bool:
    """True if fn refuses the input. A guard that never fires is not a guard."""
    try:
        fn(*args)
        return False
    except Exception:
        return True


def html_unescape_contains(page: str, s: str) -> bool:
    """The page escapes its embedded JSON, so compare against the escaped form."""
    from html import escape
    return s in page or escape(s) in page or escape(s).replace("&#x27;", "'") in page


# --------------------------------------------------------------------------
def main() -> int:
    prov = json.loads((FROZEN / "provenance.json").read_text())
    held = json.loads((FROZEN / "heldout_evaluation.json").read_text())
    pred = json.loads((FROZEN / "predictor.json").read_text())
    sens = json.loads((ROOT / "results" / "sensitivity" / "stripped_model.json").read_text())
    summary = pd.read_csv(FROZEN / "program_summary.csv")
    controls = pd.read_csv(FROZEN / "controls.csv")
    ds = prov["deciding_statistic"]
    gap = prov["gap_numbers"]

    # ---------------- 0. every shipped module must at least parse ----------------
    for f in sorted((ROOT / "src").glob("*.py")) + sorted((ROOT / "tests").glob("*.py")):
        try:
            compile(f.read_text(), str(f), "exec")
            okc, err = True, ""
        except SyntaxError as e:
            okc, err = False, f"line {e.lineno}: {e.msg}"
        check(f"{f.relative_to(ROOT)} parses", okc, err)

    # ---------------- A. the frozen numbers ----------------
    m = pd.read_csv(FROZEN / "matrix.csv", index_col=0)
    check("matrix.csv is 9,837 x 50", m.shape == (9837, 50), f"got {m.shape}")
    check("program_summary has 50 rows", len(summary) == 50, f"got {len(summary)}")

    check("adj R2 all six = 0.751", near(ds["adjusted_r2_all_six"], 0.7511),
          f"got {ds['adjusted_r2_all_six']}")
    check("adj R2 outcome-independent = 0.561",
          near(ds["adjusted_r2_x_independent_only"], 0.5606),
          f"got {ds['adjusted_r2_x_independent_only']}")
    check("program size alone explains 0.4649",
          near(sens["set_size_alone"]["r2"], 0.4649),
          f"got {sens['set_size_alone']['r2']}")
    check("post-freeze: measurement-only collapses to 0.152",
          near(sens["measurement_only_three"]["adj_r2"], 0.152),
          f"got {sens['measurement_only_three']['adj_r2']}")
    check("post-freeze: construction-only reaches 0.697",
          near(sens["construction_only_three"]["adj_r2"], 0.6965),
          f"got {sens['construction_only_three']['adj_r2']}")

    # the gate. NOTE 30 programs FAIL the gate; the "wrong 20 times" claim is the
    # 20 that fail it and still produce hits. These are different numbers.
    check("30 of 50 programs fail the measurability gate",
          gap["programs_failing_measurability_gate"] == 30,
          f"got {gap['programs_failing_measurability_gate']}")
    check("the gate is wrong 20 of 50 (fails but produces hits)",
          gap["gate_fail_but_has_hits"] == 20, f"got {gap['gate_fail_but_has_hits']}")
    check("exactly 1 of 50 passes the gate with zero hits",
          gap["gate_pass_but_zero_hits"] == 1, f"got {gap['gate_pass_but_zero_hits']}")
    check("11 of 50 programs return zero hits",
          gap["programs_with_zero_hits"] == 11, f"got {gap['programs_with_zero_hits']}")

    check("held-out balanced accuracy = 0.4375",
          near(held["axis2_balanced_accuracy"], 0.4375),
          f"got {held['axis2_balanced_accuracy']}")
    check("held-out has ZERO true positives",
          held["axis2_confusion"]["tp"] == 0, f"got {held['axis2_confusion']['tp']}")
    check("held-out Spearman rho = +0.526", near(held["axis1_spearman_rho"], 0.5257),
          f"got {held['axis1_spearman_rho']}")
    check("held-out verdict is UNDERPOWERED (1 of 10 passed the gate)",
          held["underpowered_and_inconclusive"] is True and held["n_passing_gate"] == 1,
          f"gate-passing {held['n_passing_gate']}")
    check("held-out was NOT refit", held["refit_after_seeing_results"] is False)

    ess = ds["coefficients"]["essentiality_density"]
    essp = ds["pvalues"]["essentiality_density"]
    check("essentiality coefficient is -0.021 (NEGATIVE, magnitude 0.021)",
          near(ess, -0.0206, 1e-3), f"got {ess}")
    check("essentiality p = 0.90", near(essp, 0.898, 5e-3), f"got {essp}")

    gp = controls[controls.control == "guide_pair_concordance"]
    check("guide-pair concordance control exists", len(gp) == 1)
    if len(gp):
        check("guide-pair concordance = -0.019", near(float(gp.value.iloc[0]), -0.019),
              f"got {gp.value.iloc[0]}")
    check("4 of 7 controls are FAIL and they are kept",
          int((controls.verdict == "FAIL").sum()) == 4,
          f"got {(controls.verdict=='FAIL').sum()}")

    check("scorer unchanged from the run that produced these numbers",
          prov["seal"].get("scorer_unchanged", prov["seal"].get("seal_intact")) is True)
    check("predictor was frozen before the held-out set was opened",
          pred["frozen_before_heldout_opened"] is True)
    check("held-out evaluation used the frozen predictor",
          held["predictor_sha256"].startswith("610f2a75"),
          held["predictor_sha256"][:16])

    # ---------------- B. docs trace to frozen files ----------------
    report = (ROOT / "REPORT.md").read_text()
    page = (ROOT / "index.html").read_text()
    check("index.html is standalone (figures inlined as base64)",
          "base64," in page, "figures must be embedded, not linked")
    # The page is now interactive. The constraint that matters at an expo is not
    # "no controls" but "nothing that can fail unattended" -- so: no network.
    for pat, label in [(r"\bfetch\s*\(", "fetch()"),
                       (r"XMLHttpRequest", "XMLHttpRequest"),
                       (r"<script[^>]+src=", "external script"),
                       (r'src="https?://', "remote asset"),
                       (r'<link[^>]+href="https?://', "remote stylesheet")]:
        check(f"page makes no network call: {label}",
              not re.search(pat, page, re.I))
    check("explorer data is embedded, not fetched", "const DATA = [" in page)
    # The page went up on GitHub Pages, which made "there is no hosted instance"
    # false everywhere it was written. The offline property is still true and is
    # still the point -- a single static file with everything inlined -- but it
    # has to be claimed as "no backend", not "not hosted". Nothing was checking
    # the difference, so the sentence sat there wrong.
    for label, txt in [("index.html", page),
                       ("README.md", (ROOT / "README.md").read_text())]:
        stale = re.search(r"no hosted instance|nothing hosted(?![^.]*MCP)", txt, re.I)
        ok = stale is None or "mcp" in txt[max(0, stale.start() - 220):stale.end() + 80].lower()
        check(f"no stale 'not hosted' claim in {label}", ok,
              txt[max(0, stale.start() - 60):stale.end() + 60].replace("\n", " ") if stale and not ok else "")
    check("all 50 programs embedded in the explorer",
          page.count('"program":"HALLMARK_') == 50,
          f"got {page.count(chr(34) + 'program' + chr(34) + ':' + chr(34) + 'HALLMARK_')}")
    check("gate-fail-with-hits rows match provenance",
          page.count('"gate_fail_with_hits":true') == gap["gate_fail_but_has_hits"],
          f"page {page.count(chr(34)+'gate_fail_with_hits'+chr(34)+':true')} vs frozen {gap['gate_fail_but_has_hits']}")
    caps = (FIGS / "CAPTIONS.md").read_text()
    both = report + page + caps

    traced = {
        "0.751": ds["adjusted_r2_all_six"], "0.561": ds["adjusted_r2_x_independent_only"],
        "46.5": round(sens["set_size_alone"]["r2"] * 100, 1),
        "0.4375": held["axis2_balanced_accuracy"],
        "0.152": sens["measurement_only_three"]["adj_r2"],
        "0.697": sens["construction_only_three"]["adj_r2"],
    }
    for text, frozen in traced.items():
        present = text in both
        matches = near(float(text), float(frozen), 6e-3) or \
            near(float(text) / 100, float(frozen), 6e-3)
        check(f"'{text}' in docs traces to a frozen value", present and matches,
              f"in docs={present} frozen={frozen}")

    # docs use a Unicode minus; the CSVs use an ASCII hyphen. Normalise both.
    norm = lambda x: x.replace("\u2212", "-").replace("\u2013", "-")
    for n in ["9,837", "20 of 50", "-0.019", "0.4375"]:
        check(f"headline '{n}' appears in REPORT.md", norm(n) in norm(report))

    # ---------------- C. the scope rule, enforced ----------------
    # No NOVEL gene may be named. A known gene may appear only as a recovered
    # known answer. Scan the page text and the captions for gene symbols sitting
    # next to verdict language.
    gmt = ROOT / "data" / "genesets" / "h.all.v2026.1.Hs.symbols.gmt"
    universe = set()
    for line in gmt.read_text().splitlines():
        universe.update(line.split("\t")[2:])
    universe = {g for g in universe if len(g) >= 4}          # avoid 2-3 char noise

    VERDICT = re.compile(
        r"\b(novel|discover\w*|candidate|nominat\w*|new target|we found|"
        r"identif\w+|driver|our (?:hit|target)|promising)\b", re.I)
    ALLOWED = re.compile(
        r"(recovered known answer|textbook|not claim\w*|do not claim|"
        r"positive control|control,? not|known regulator|canonical)", re.I)

    def scan(label: str, text: str) -> None:
        hits = []
        for g in universe:
            for mt in re.finditer(rf"\b{re.escape(g)}\b", text):
                w = text[max(0, mt.start() - 260): mt.end() + 260]
                if VERDICT.search(w) and not ALLOWED.search(w):
                    hits.append(f"{g}: …{w[230:330].strip()}…")
        check(f"scope rule: no gene named as a finding in {label}", not hits,
              hits[0] if hits else "")

    # ---- the registry of RENDERED SURFACES ----
    # Every surface an audience reads is registered here once, and both guards
    # below iterate the registry. app.py was scanned by neither for most of this
    # project's life: the guards named index.html and CAPTIONS.md literally, so
    # the Streamlit page kept saying a program was "sealed in git before the
    # scoring code existed" long after that framing was stripped everywhere a
    # guard could see. The registry exists so a surface is covered by every
    # guard or by none, never by some.
    #
    # app.py is scanned for what the audience READS, not for its Python. Two
    # things are stripped first because neither reaches the screen: f-string
    # expressions, since {prereg['commit']} renders a commit hash; and
    # dict-subscript keys, since prov["seal"] is a lookup into a frozen file
    # whose key we do not rename.
    app_src = (ROOT / "app.py").read_text()
    app_text = re.sub(r"<[^>]+>", " ",
                      re.sub(r"\[\s*['\"][^'\"]*['\"]\s*\]", " ",
                             re.sub(r"\{[^{}]*\}", " ",
                                    re.sub(r"<style.*?</style>", " ",
                                           app_src, flags=re.S))))
    page_text = re.sub(r"<[^>]+>", " ", re.sub(r"<style.*?</style>|<img[^>]*>", " ", page, flags=re.S))

    # audit.html is the drop-a-CSV surface. It is scanned for what a reader sees:
    # <script> goes with <style> because the largest script on that page is the
    # denali_audit source inlined verbatim so the browser can run the real
    # package, and that source is code the machine executes, not prose an
    # audience reads -- the same reason app.py above is stripped of its
    # f-string expressions. The inlined copy is guarded for drift instead, by
    # tests/test_cross_surface.py, which requires it byte-identical to the
    # package.
    audit_page = (ROOT / "audit.html")
    audit_text = re.sub(r"<[^>]+>", " ",
                        re.sub(r"<style.*?</style>|<script.*?</script>", " ",
                               audit_page.read_text(), flags=re.S)) if audit_page.exists() else ""

    SURFACES = {
        "index.html": page_text,
        "audit.html": audit_text,
        "app.py": app_text,
        "results/figures/CAPTIONS.md": caps,
        "REPORT.md": report,
    }

    for label, txt in SURFACES.items():
        scan(label, txt)

    # framing rule: the project does not lead with commit ordering
    SEAL = re.compile(r"\bseal(ed|ing)?\b|before the scoring code existed|"
                      r"\d+ minutes? before", re.I)
    for label, txt in SURFACES.items():
        hit = SEAL.search(txt)
        check(f"no seal framing in {label}", hit is None,
              txt[max(0, hit.start()-60):hit.end()+60].replace("\n", " ") if hit else "")

    # A NEW surface must be registered above, or this fails. Without this, the
    # next page someone adds repeats app.py's history exactly: rendered to an
    # audience, read by no guard, and green the whole time.
    rendered = set()
    for h in ROOT.glob("*.html"):
        rendered.add(h.name)
    for py in ROOT.glob("*.py"):
        if re.search(r"^import streamlit|^\s*import streamlit", py.read_text(), re.M):
            rendered.add(py.name)
    for py in sorted((ROOT / "src").glob("*.py")):
        for out in re.findall(r"['\"]([\w./-]+\.html)['\"]", py.read_text()):
            rendered.add(Path(out).name)
    unregistered = sorted(rendered - set(SURFACES))
    check("every rendered surface is registered with the scope guards",
          not unregistered,
          f"unguarded: {unregistered} -- add to SURFACES in this file so the "
          f"gene-naming and framing guards read it too")

    # The seal guard above scans rendered TEXT. Two figures had "SEALED program"
    # drawn into the PNG, where no text scan can reach it -- the guard passed for
    # weeks while the framing sat in the two most prominent images on the page.
    # Pixels cannot be scanned, so scan the code that draws them.
    figsrc = (ROOT / "src" / "figures_matrix.py").read_text()
    for m in re.finditer(r'["\']([^"\']*)["\']', figsrc):
        if SEAL.search(m.group(1)):
            check("no seal framing baked into a figure label", False, m.group(1)[:70])
            break
    else:
        check("no seal framing baked into a figure label", True)
    check("figure inputs are in-repo, not absolute paths",
          not re.search(r'Path\(\s*["\']/', figsrc),
          "an absolute path breaks make all on every other machine")

    check("scope limit is stated on the page", "-0.019" in page or "\u22120.019" in page)
    check("scope limit is stated in the captions",
          "gene-level" in caps or "0.019" in caps or "pointer layer" in caps)

    # ---------------- D. the tool-chain strip ----------------
    # The page says the callable surface reports its own failure verbatim. That
    # is only true if the page and the server read the same string object, so
    # check the object, not a lookalike substring.
    sys.path.insert(0, str(ROOT))
    from src.answers import SCOPE, VALIDATION, unscored          # noqa: E402
    wire = unscored("HALLMARK_A_PROGRAM_WE_NEVER_SCORED", pred["residual_sd"])
    for label, s in [("predictor_validation", VALIDATION), ("scope_limit", SCOPE)]:
        check(f"page quotes the server's {label} verbatim",
              html_unescape_contains(page, s), s[:52] + "\u2026")
    # The refusal path and the lookup path must normalise the same way. They
    # drifted once: refuse() was made case-insensitive while the program lookup
    # stayed exact, so a lowercase name returned UNSCORED -- a confident wrong
    # answer rather than a refusal, which is the worse failure of the two.
    import importlib
    _mcp = importlib.import_module("src.mcp_server")
    _canon = str(summary.program.iloc[0])
    _forms = [_canon, _canon.lower(), _canon.title(), f"  {_canon.lower()}  "]
    _got = [_mcp.reversibility(f) for f in _forms]
    check("MCP lookup normalises case the same way the refusals do",
          all(g.get("status") == "MEASURED" and g.get("program") == _canon
              for g in _got),
          f"{[g.get('status') for g in _got]} for {len(_forms)} spellings of one name")
    check("MCP still refuses a gene symbol in any case",
          all(_mcp.reversibility(s).get("status") == "REFUSED"
              for s in ("SREBF2", "srebf2", "SrebF2")))
    check("MCP still reports a genuinely unscored program as UNSCORED",
          _mcp.reversibility("HALLMARK_NOT_A_REAL_PROGRAM").get("status") == "UNSCORED")

    check("the server volunteers its failure unasked",
          wire["predictor_validation"] is VALIDATION and "worse than chance" in VALIDATION)
    check("the wire example carries the frozen balanced accuracy",
          f"{held['axis2_balanced_accuracy']:.4f}" in VALIDATION, VALIDATION)

    # "Touched a number" is a claim about this repository, so run the grep the
    # page invites a reviewer to run. Scope it to what `make all` actually runs:
    # src/modal_sweep.py imports modal by design, but it REPRODUCES the frozen
    # files rather than producing them, and it is deliberately not a make-all
    # step. That distinction is the whole claim, so assert it rather than
    # loosening the guard until it passes.
    mk = (ROOT / "Makefile").read_text()
    all_block = mk.split("all:")[1].split("\n\n")[0] if "all:" in mk else mk
    pipeline_mods = set(re.findall(r"-m\s+src\.(\w+)", all_block))
    check("make all runs a non-empty module list", len(pipeline_mods) >= 5,
          f"found {sorted(pipeline_mods)}")
    check("modal_sweep is NOT a make-all step (it verifies, it does not produce)",
          "modal_sweep" not in pipeline_mods)
    # The second Modal entry point runs a post-hoc arm over the published corpus.
    # It is held to the same rule for the same reason: cloud compute is allowed to
    # reproduce or extend, never to produce a committed result on a path a clean
    # clone cannot re-run without an account.
    check("modal_corpus_rerank is NOT a make-all step either",
          "modal_corpus_rerank" not in pipeline_mods)
    _mcr = ROOT / "src" / "modal_corpus_rerank.py"
    if _mcr.exists():
        _src = _mcr.read_text()
        check("the Modal corpus arm imports the local arm rather than reimplementing it",
              "from src.corpus_rerank import screen_row" in _src)
        # Prose is allowed to SAY "results/frozen/ is untouched"; code is not
        # allowed to name it. Strip the docstrings and comments and look at what
        # actually executes -- the first version of this check failed on its own
        # module's disclaimer, which is a guard measuring the wrong thing.
        # `ast` is rebound later inside this function, so it is local here --
        # alias the module rather than reorder someone else's imports.
        import ast as _ast
        _tree = _ast.parse(_src)
        for _n in _ast.walk(_tree):                  # drop every docstring
            _b = getattr(_n, "body", None)
            if isinstance(_n, (_ast.Module, _ast.FunctionDef, _ast.AsyncFunctionDef,
                               _ast.ClassDef)) and _b and isinstance(
                                   _b[0], _ast.Expr) and isinstance(
                                   _b[0].value, _ast.Constant) and isinstance(
                                   _b[0].value.value, str):
                _n.body = _b[1:] or [_ast.Pass()]
        _code = _ast.unparse(_tree)
        check("the Modal corpus arm never writes results/frozen/",
              "frozen" not in _code, "code path mentions the frozen interface")
        check("the Modal corpus arm writes its own file, not the local arm's",
              "modal_agreement.json" in _src and 'out / "corpus_rerank.json"' not in _src)
    # concordance READS results/rpe1/. For hours make all ran concordance without
    # regenerating its input, so a clean clone silently consumed a committed file
    # instead of reproducing it. Order matters, so assert the order.
    _order = re.findall(r"-m\s+src\.(\w+)", all_block)
    if "concordance" in _order:
        check("make all regenerates the RPE1 arm before concordance reads it",
              "rpe1_arm" in _order
              and _order.index("rpe1_arm") < _order.index("concordance"),
              f"order: {_order[-6:]}")
    check("annotation_arm is NOT a make-all step (it needs Modal)",
          "annotation_arm" not in pipeline_mods)

    src_text = "\n".join((ROOT / "src" / f"{m}.py").read_text()
                         for m in sorted(pipeline_mods)
                         if (ROOT / "src" / f"{m}.py").exists())
    for tool in ["modal", "esm", "benchflow", "benchling", "paperclip"]:
        used = re.search(rf"^\s*(?:import|from)\s+{tool}\b", src_text, re.I | re.M)
        check(f"no make-all module imports {tool} -- 'touched a number: no' holds",
              used is None, used.group(0).strip() if used else "")

    # ---------------- E. the post-freeze VIF check ----------------
    # Verified twice by independent implementations; these lock the values and
    # the framing. The check must never present itself as pre-registered, and
    # log-VIF must only ever be compared to the UPPER bound -- it inherits
    # coherence's partial circularity.
    vif_p = ROOT / "results" / "sensitivity" / "vif_camera.json"
    if vif_p.exists():
        vif = json.loads(vif_p.read_text())
        a = vif["adj_r2"]
        check("VIF: log-VIF alone = 0.726", near(a["log_vif_alone"], 0.7257),
              f"got {a['log_vif_alone']}")
        check("VIF: all-six reference matches the frozen headline",
              near(a["all_six_features"], ds["adjusted_r2_all_six"], 1e-3),
              f"{a['all_six_features']} vs frozen {ds['adjusted_r2_all_six']}")
        check("VIF: coherence-flattened bound = 0.463",
              near(a["vif_coherence_flattened"], 0.4629),
              f"got {a['vif_coherence_flattened']}")
        check("VIF: labelled post-freeze, not pre-registered",
              "NOT PRE-REGISTERED" in vif.get("status", ""))
        check("VIF: circularity comparison rule is stated",
              "UPPER bound" in vif.get("comparison_rule", ""))
        check("VIF: does not claim to replace the primary",
              "pre-registered primary" in vif.get("does_not_replace", ""))
        check("VIF: cites the external theory (Wu & Smyth 2012)",
              "10.1093/nar/gks461" in vif.get("citation", ""))

    # The Modal run's own claim is that it reproduces the frozen numbers. Do not
    # take its word for it either -- it writes a verdict and this reads it back.
    agree = ROOT / "results" / "modal" / "agreement.json"
    if agree.exists():
        a = json.loads(agree.read_text())
        check("Modal reproduced all 50 programs from the frozen result",
              a["reproduces_frozen"] and a["n_programs"] == 50
              and not a["mismatched_columns"], str(a.get("mismatched_columns")))

    # A frozen artifact with a timing field cannot be byte-compared across
    # machines, which is exactly what the reproduction check does.
    for jf in sorted(FROZEN.glob("*.json")):
        txt = jf.read_text()
        check(f"{jf.name} carries no wall-clock field",
              "wall_clock" not in txt and "elapsed" not in txt)

    # FIG 4 drew its lines in set-iteration order, so the same picture produced
    # different bytes per process. Both orderings must now be sorted.
    fm = (ROOT / "src" / "figures_matrix.py").read_text()
    check("fig4 sorts before drawing (no per-process PNG drift)",
          "sorted(gs)" in fm and "-len(kv[1]), kv[0]" in fm)

    # ---------------- G. the portable audit ----------------
    # audit_screen.py runs this project's check on somebody else's screen. It is
    # the only thing here that claims to generalise, so it is tested on data it
    # has never seen: two synthetic screens with known answers, one confounded by
    # construction and one clean. If it cannot tell those apart it is useless.
    from src.audit_screen import audit                          # noqa: E402
    rng = __import__("numpy").random.default_rng(20260815)
    sz = rng.integers(10, 300, 60)
    conf = audit(sz, (sz * rng.uniform(1.5, 3.0, 60)).astype(int))
    clean = audit(sz, rng.integers(0, 400, 60))
    check("audit flags a size-confounded screen", conf["verdict"] == "CONFOUNDED",
          f"r2={conf['r2_size_alone']}")
    check("audit clears a screen that is not size-driven",
          clean["verdict"] == "NOT SIZE-DOMINATED", f"r2={clean['r2_size_alone']}")
    check("audit reproduces our own frozen size-alone value",
          near(audit(summary.n_present, summary.n_hits_q05)["r2_size_alone"],
               sens["set_size_alone"]["r2"], 5e-3))

    # ---------------- G1. the study and the product are ONE implementation ----
    # There used to be two copies of audit(): this file's and the package's. They
    # agreed on the day they were written and nothing checked that they still did
    # -- the package's anti-drift test pinned the package against 0.4649 and never
    # against src/. src/audit_screen.py now IMPORTS the packaged function, so the
    # study runs on its own product. These checks assert that structurally, so a
    # future edit that re-copies the forty lines back into src/ fails here rather
    # than passing quietly and diverging later.
    import denali_audit.core as _pkg_core                       # noqa: E402
    from src import audit_screen as _as                         # noqa: E402
    check("the study's audit() IS the packaged audit(), not a copy of it",
          _as.audit is _pkg_core.audit,
          f"{_as.audit.__module__} vs {_pkg_core.audit.__module__}")
    check("src/audit_screen.py defines no second audit()",
          "def audit(" not in (ROOT / "src" / "audit_screen.py").read_text())
    # Belt and braces: even if someone reintroduces a copy, the outputs must match
    # key-for-key on the frozen data. The packaged one may add keys (corpus
    # context); it may not disagree on one they share.
    _a = _as.audit(summary.n_present, summary.n_hits_q05, summary.coherence)
    _b = _pkg_core.audit(summary.n_present, summary.n_hits_q05, summary.coherence)
    _differ = [k for k in _a if k in _b and _a[k] != _b[k]]
    check("study and package agree on every shared key of audit()", not _differ,
          f"disagree on {_differ}" if _differ else f"{len(set(_a) & set(_b))} keys identical")

    # The ONE deliberate second implementation is results/independent/ --
    # src/independent_recompute.py, written from the method section without
    # reading the original and using different libraries at every step. It exists
    # to be different; agreement with it is evidence. That is the opposite of the
    # duplication removed above, and both files must keep saying so, because a
    # reader who confuses the two will "helpfully" delete the wrong one.
    _ind = (ROOT / "src" / "independent_recompute.py").read_text()
    check("the independent reimplementation still declares itself deliberate",
          "INDEPENDENT second implementation" in _ind and "were not read" in _ind)
    check("audit_screen.py distinguishes itself from that reimplementation",
          "independent_recompute.py" in (ROOT / "src" / "audit_screen.py").read_text())

    # audit_replication() is the exception, and it is pinned rather than shared.
    # The two are NOT copies: the study residualises on raw size, the package on
    # log10(size), so they return different numbers on the same input. Each
    # already carries a frozen surface (evaluation 6's published 26% here,
    # `denali audit --hits-b` there), so unifying them would move a published
    # number after the fact. Pinning both is what stops the gap widening unseen.
    _pp = pd.read_csv(ROOT / "results" / "concordance" / "paired_programs.csv")
    _rs = _as.audit_replication(_pp.n_present_k562, _pp.n_hits_q05_k562,
                                _pp.n_hits_q05_rpe1)
    _rp = _pkg_core.audit_replication(_pp.n_present_k562, _pp.n_hits_q05_k562,
                                      _pp.n_hits_q05_rpe1)
    check("both replication auditors still agree on RAW agreement",
          near(_rs["raw_agreement_spearman"], _rp["agreement_raw"], 1e-4),
          f"{_rs['raw_agreement_spearman']} vs {_rp['agreement_raw']}")
    check("study replication auditor pinned at its published value",
          near(_rs["agreement_after_removing_size"], 0.4934, 1e-3),
          f"{_rs['agreement_after_removing_size']}")
    check("packaged replication auditor pinned at its own, different value",
          near(_rp["agreement_after_removing_size"], 0.4507, 1e-3),
          f"{_rp['agreement_after_removing_size']}")
    check("the divergence between them is documented in both files",
          "0.4507" in (ROOT / "src" / "audit_screen.py").read_text()
          and "0.4934" in (ROOT / "packages" / "denali-audit" / "denali_audit"
                           / "core.py").read_text())

    # ---------------- G2. evaluation 8, the off-target arm ----------------
    # Two published datasets, neither ours. The source workbooks are git-ignored,
    # so these checks are skipped on a clone that has not fetched them -- but the
    # committed JSON is always checked for labelling, and the numbers are
    # recomputed from the sheets whenever they are present.
    off_p = ROOT / "results" / "offtarget" / "offtarget_evaluation.json"
    if off_p.exists():
        off = json.loads(off_p.read_text())
        a1, a2 = off["arm1_assay_concordance"], off["arm2_variant_driven_sites"]

        check("offtarget: labelled post-hoc with thresholds swept",
              "POST-HOC" in off["status"] and "SWEPT" in off["status"],
              off["status"])
        check("offtarget: does not revise the frozen primary",
              "results/frozen/" in off["does_not_revise"])

        # the sweep must actually be a sweep, not one threshold with a range glued on
        shares = [s["share_of_agreement_that_is_search_yield"]
                  for s in a1["sweep"] if "share_of_agreement_that_is_search_yield" in s]
        check("offtarget: every hit rule in the sweep produced a result",
              len(shares) == len(a1["hit_rules_swept"]),
              f"{len(shares)} of {len(a1['hit_rules_swept'])} rules scored")
        rng_ = a1["share_of_agreement_that_is_search_yield"]
        check("offtarget: the reported share range spans the whole sweep",
              near(rng_["min"], min(shares), 1e-9) and near(rng_["max"], max(shares), 1e-9),
              f"reported {rng_['min']}-{rng_['max']} vs sweep {min(shares)}-{max(shares)}")

        # The tautological direction must stay disclosed. It is the number this
        # arm would have overstated itself with: at the lowest thresholds a
        # nominated site with >=1 read is a hit by construction, so R2 is exactly 1.
        taut = a1["r2_tautological_biochemical_direction"]
        check("offtarget: the circular regression is disclosed, not dropped",
              "a_tautology_we_refused_to_report" in a1 and len(taut) == len(shares))
        check("offtarget: the circular direction really is degenerate",
              max(taut) >= 0.99 and max(taut) > max(
                  s["r2_search_yield_predicts_cellular_hits"] for s in a1["sweep"]
                  if "r2_search_yield_predicts_cellular_hits" in s),
              f"tautological max {max(taut)}")

        # arm 2: the two fractions are different quantities and must stay separate
        alt, absent = a2["alt_allele_best_alignment"], a2["absent_from_reference"]
        check("offtarget: alt-allele and absent-from-reference are reported apart",
              alt["fraction"] > absent["fraction"] * 2,
              f"{alt['fraction']} vs {absent['fraction']}")
        check("offtarget: the ranked denominator is stated",
              "RANKED SELECTION" in a2["denominator_warning"])
        check("offtarget: recovering CRISPRme's own finding is not called new",
              "not a discovery" in a2["not_a_discovery"].lower()
              or "is not presented as new" in a2["not_a_discovery"])

        # no guide may be named safe or unsafe -- the gene-symbol scope rule,
        # applied to guides, in a domain where the ranking has a patient at the end
        # Same shape as the gene-symbol guard: a verdict word is only a violation
        # when it is NOT sitting inside a refusal. The disclaimers necessarily
        # contain the words they forbid.
        blob = json.dumps(off).lower()
        SAFEWORD = re.compile(r"\b(safe|unsafe|safest|riskiest|recommend\w*|"
                              r"best guide|worst guide|use this guide)\b")
        REFUSAL = re.compile(r"(no guide is named|named safe or unsafe|would be "
                             r"committing|not a recommendation|none is ranked|"
                             r"not verdicts|refus\w+)")
        bad = [m.group(0) for m in SAFEWORD.finditer(blob)
               if not REFUSAL.search(blob[max(0, m.start() - 200):m.end() + 200])]
        check("offtarget: no guide is named safe or unsafe", not bad, str(bad[:3]))

        # --- recompute the fractions ---
        # These recompute from the COMMITTED per-guide table, not from the source
        # workbooks, and that is deliberate. The workbooks are git-ignored, so a
        # check gated on their presence runs here and not in CI -- which makes the
        # suite's own count depend on whether optional data happens to be on disk,
        # and a self-counting badge cannot have an environment-dependent count.
        # The first version of these checks did exactly that: 307 locally, 305 on
        # a clone. Every check below runs everywhere.
        pg = pd.read_csv(ROOT / "results" / "offtarget" / "crisprme_per_guide.csv")
        tot = int(pg.n_sites_ranked.sum())
        alt_n = int(pg.alt_allele_best_alignment.sum())
        abs_n = int(pg.absent_from_reference.sum())
        check("offtarget: the alt-allele fraction recomputes per guide",
              alt_n == alt["n"] and near(alt_n / tot, alt["fraction"], 5e-4),
              f"recomputed {alt_n}/{tot}={alt_n / tot:.4f} vs "
              f"{alt['n']}/{a2['sites_ranked_total']}={alt['fraction']}")
        check("offtarget: the absent-from-reference fraction recomputes per guide",
              abs_n == absent["n"] and near(abs_n / tot, absent["fraction"], 5e-4),
              f"recomputed {abs_n}/{tot}={abs_n / tot:.4f} vs {absent['fraction']}")
        check("offtarget: the per-guide table covers every guide in the JSON",
              len(pg) == a2["guides"] and tot == a2["sites_ranked_total"],
              f"csv {len(pg)} guides / {tot} sites vs json {a2['guides']} / "
              f"{a2['sites_ranked_total']}")

        # The source workbooks are git-ignored, so pin them by hash instead: a
        # silently re-versioned supplement would otherwise be undetectable.
        offdoc = (ROOT / "docs" / "OFFTARGET.md").read_text()
        check("offtarget: both source workbooks are pinned by sha256",
              len(re.findall(r"\b[0-9a-f]{64}\b", offdoc)) >= 2,
              f"found {len(re.findall(r'[0-9a-f]{64}', offdoc))} hashes in docs/OFFTARGET.md")

        # --- ported from the offtarget-arm branch before deleting it ---
        # That branch was a parallel preservation of this same arm (identical
        # JSON, script and both CSVs), so it was not merged. These three checks
        # were the part of it this suite did not already have.

        # The JSON promises it does not revise the freeze. This checks the CODE
        # cannot: every write call in the arm must target OUT. Searching for the
        # bare path would fire on the honest does_not_revise disclosure, which
        # names results/frozen/ deliberately -- so inspect the writes, not the
        # mentions.
        arm_src = (ROOT / "src" / "offtarget_audit.py").read_text()
        writes = [ln.strip() for ln in arm_src.splitlines()
                  if any(w in ln for w in ("to_csv(", "write_text(", "to_json(",
                                           "savefig(", "open("))]
        stray = [ln for ln in writes if "OUT /" not in ln]
        check("offtarget: every write in the arm targets results/offtarget/",
              bool(writes) and not stray,
              " | ".join(ln[:60] for ln in stray) or f"{len(writes)} writes, all to OUT")

        # The JSON and the CSV are two renderings of one sweep. If they drift,
        # a reader gets a different answer depending on which file they open.
        sweep_csv = pd.read_csv(ROOT / "results" / "offtarget" / "changeseq_sweep.csv")
        json_thr = [r["read_threshold"] for r in a1["sweep"]]
        json_shr = [r["share_of_agreement_that_is_search_yield"] for r in a1["sweep"]]
        check("offtarget: the JSON sweep and the sweep CSV agree row-for-row",
              json_thr == sweep_csv.read_threshold.tolist()
              and all(near(a, b, 1e-9) for a, b in
                      zip(json_shr, sweep_csv.share_of_agreement_that_is_search_yield)),
              f"json {json_thr} vs csv {sweep_csv.read_threshold.tolist()}")
        check("offtarget: the swept rules in the JSON match the declared rules",
              json_thr == a1["hit_rules_swept"],
              f"sweep {json_thr} vs declared {a1['hit_rules_swept']}")

    # ---------------- G3. evaluation 9, the Adamson engagement arm ----------------
    # This arm amended its own pre-registration mid-flight, which is the single
    # most abusable thing in this repo: an amendment is how you launder a
    # threshold you did not like. The amendment here is clean, and these checks
    # are what stop it quietly becoming unclean later. The arm shipped with no
    # invariants of its own.
    ad_p = ROOT / "results" / "adamson" / "adamson_evaluation.json"
    if ad_p.exists():
        ad = json.loads(ad_p.read_text())
        pre_txt = (ROOT / "docs" / "ADAMSON_PREREG.md").read_text()

        # The pre-registration is in two parts and only the second may be new.
        head, sep, tail = pre_txt.partition("# AMENDMENT 1")
        check("adamson: the amendment is appended below the original, not woven in",
              bool(sep) and len(head) > 1000 and "AMENDMENT" not in head)
        check("adamson: the amendment is dated",
              re.search(r"# AMENDMENT 1 — 20\d\d-\d\d-\d\d", pre_txt) is not None)
        check("adamson: the amendment states it changed no threshold",
              "no\nthreshold anywhere in this document is changed" in tail
              or "no threshold" in tail.split("\n\n")[1].lower())

        # Verify the amendment's provenance claim rather than believing its prose:
        # the text above the amendment line must still hash to the sha256 the
        # amendment cites. CONTENT-ADDRESSED ON PURPOSE. The first version of this
        # check ran `git show <sha>:docs/ADAMSON_PREREG.md`, and that sha stopped
        # existing the moment the branch was rebased and deleted -- so the check
        # silently skipped in a fresh clone and the suite counted 350 there against
        # 351 here. A guard that needs a particular commit to exist is a guard that
        # disappears when history is rewritten; hashing the bytes needs no history
        # at all.
        import hashlib
        cited = re.search(r"sha256 `([0-9a-f]{8})…`", tail)
        original_text = head.rstrip().removesuffix("---").rstrip() + "\n"
        digest = hashlib.sha256(original_text.encode()).hexdigest()
        check("adamson: the pre-amendment text still hashes to the cited sha256",
              cited is not None and digest.startswith(cited.group(1)),
              f"computed {digest[:16]} vs cited {cited.group(1) if cited else 'none'}")

        # The frozen scorer ran unmodified, but the substrate construction is new
        # code. Conflating those would let "we reused the frozen scorer" cover a
        # step the hash never saw.
        check("adamson: the frozen scorer hash is the real one",
              ad["scorer_sha256"].startswith("2abfdc6f"), ad["scorer_sha256"][:16])
        check("adamson: construction is declared OUTSIDE the scorer's hash",
              ad["substrate_construction_covered_by_scorer_hash"] is False)
        res_txt = (ROOT / "docs" / "ADAMSON_RESULTS.md").read_text()
        check("adamson: the writeup names the construction step, not a bare rerun",
              "plus a pre-registered construction step we" in res_txt
              and 'not** "an\nunmodified rerun."' in res_txt.replace("\r", ""))
        check("adamson: it refuses the replication framing",
              "NOT a replication" in ad["scope"])
        check("adamson: does not revise the frozen primary",
              "results/frozen/" in ad["does_not_revise"])

        # The result itself: the confound has to survive engagement for the arm
        # to mean anything, and the K562 comparator must be the frozen one.
        check("adamson: the engagement premise was established before the test",
              ad["p0_engagement"]["established"] is True)
        check("adamson: the K562 comparator is the frozen size-alone value",
              near(ad["k562_size_alone_r2_for_reference"],
                   sens["set_size_alone"]["r2"], 5e-3),
              f"{ad['k562_size_alone_r2_for_reference']} vs "
              f"{sens['set_size_alone']['r2']}")
        check("adamson: the control-choice sensitivity is reported, not hidden",
              len(ad["control_choice_sensitivity"]["per_single_control"]) >= 2)

    check("audit refuses to rank or recommend",
          "not a candidate list" in conf["what_this_is_not"].lower()
          and not any("rank_" in k or k == "top" for k in conf))
    check("audit needs enough sets to say anything",
          _raises(audit, [10, 20, 30], [1, 2, 3]))

    # ---------------- H. the unstressed-cell-line bound ----------------
    # The sharpest question asked of this project: is the headline really the
    # unstressed-K562 problem wearing the size problem's clothes? These lock the
    # answer and, more importantly, the honesty of its scope.
    eb_p = ROOT / "results" / "sensitivity" / "engagement_bound.json"
    if eb_p.exists():
        eb = json.loads(eb_p.read_text())
        mb = eb["measurable_but_not_engaged"]
        recomputed = int((summary.passes_measurability_gate
                          & (summary.n_hits_q05 == 0)).sum())
        check("engagement: measurable-but-not-engaged count matches the frozen table",
              mb["n"] == recomputed == gap["gate_pass_but_zero_hits"],
              f"json {mb['n']}, recomputed {recomputed}")
        check("engagement: removing them does not rescue the result",
              abs(eb["delta"]) < 0.02, f"delta {eb['delta']}")
        check("engagement: the size effect is the larger one",
              eb["size_alone_r2_all_programs"] > 4 * abs(eb["delta"]))
        check("engagement: labelled post-freeze",
              "NOT PRE-REGISTERED" in eb.get("status", ""))
        check("engagement: states what it cannot settle",
              "cannot bound it across screens" in eb.get("what_this_does_not_settle", ""))

    # ---------------- I. the frozen proposals (Rachel's expo layer) ----------------
    # proposals.json is a frozen artifact the page renders, so it gets the same
    # treatment as every other one: the branches must be chosen by measured value
    # rather than by name, and nothing in it may read as a nomination.
    prop_p = FROZEN / "proposals.json"
    if prop_p.exists():
        prop = json.loads(prop_p.read_text())
        check("proposals: one per branch of next_experiment",
              {"null", "hit", "unscored"} <= set(prop),
              f"got {sorted(k for k in prop if not k.startswith('_'))}")
        # each pick must be re-derivable from the frozen table, not hardcoded
        null_p = summary[summary.n_hits_q05 == 0].nlargest(1, "n_present").iloc[0].program
        check("proposals: the NULL branch is chosen by measured value",
              prop["null"]["program"] == null_p,
              f"json {prop['null']['program']} vs recomputed {null_p}")
        hit_p = summary.nlargest(1, "R_p").iloc[0].program
        check("proposals: the HIT branch is the top measured R_p",
              prop["hit"]["program"] == hit_p,
              f"json {prop['hit']['program']} vs recomputed {hit_p}")
        check("proposals: outcomes are the three real branches",
              {prop[k]["outcome"] for k in ("null", "hit", "unscored")} ==
              {"NULL_WITH_MECHANISM", "HIT_ABOVE_THRESHOLD", "UNSCORED"})
        check("proposals: the unscored branch keeps its observed outcome",
              "observed_outcome" in prop["unscored"]
              and prop["unscored"]["observed_outcome"]["n_hits_q05"] == 0)
        blob = json.dumps(prop).lower()
        check("proposals: no nomination language",
              not any(w in blob for w in ("we recommend", "top candidate",
                                          "most promising", "best target")))

        # THE ONE THAT WAS MISSING. proposals.json went stale at 24cf2ba and stayed
        # stale for hours: what_would_change_my_mind landed in next_experiment.py at
        # 0dfb5d2 and the freeze step was never re-run. Nothing noticed, because
        # every check above interrogates the file's CONTENT and none of them asked
        # whether the file still matches the generator that owns it. So `make all`
        # on a clean clone rewrote it and left the tree dirty, which made README's
        # byte-identical reproduction claim false while the whole suite stayed green.
        #
        # A frozen artifact that its own generator would rewrite is not frozen. This
        # regenerates in memory -- writing nothing -- and demands byte equality.
        # The generator is pointed at a temp directory holding copies of its two
        # inputs, so this check never writes a byte into results/frozen/ -- a test
        # that had to mutate the frozen interface to verify it would be its own
        # counterexample.
        import contextlib
        import io
        import shutil
        import tempfile

        from src import freeze_proposals as _fp

        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            for f in ("program_summary.csv", "heldout.csv"):
                shutil.copy2(FROZEN / f, tmp / f)
            real_frozen = _fp.FROZEN
            try:
                _fp.FROZEN = tmp
                with contextlib.redirect_stdout(io.StringIO()):
                    _fp.main()
                regenerated = (tmp / "proposals.json").read_bytes()
            finally:
                _fp.FROZEN = real_frozen
        check("proposals: the frozen file matches what its generator produces",
              prop_p.read_bytes() == regenerated,
              "results/frozen/proposals.json is STALE -- run "
              "`python -m src.freeze_proposals`. A clean clone would rewrite it, "
              "so the byte-identical reproduction claim is false until you do.")

    # ---------------- J. program A is described correctly ----------------
    # REPORT.md claimed inducing ER stress would move program A "from 0 hits to
    # non-zero". It has 517. The null is real but it is the known-regulator
    # control failing, not an absence of hits -- two different findings that had
    # been collapsed into one sentence for hours. Nothing was watching prose
    # claims about a specific program, so now something is.
    readme_txt = (ROOT / "README.md").read_text()
    a_row = summary[summary.is_program_A]
    if len(a_row):
        a = a_row.iloc[0]
        for label, txt in [("REPORT.md", report), ("README.md", readme_txt)]:
            bad = re.search(r"UPR from 0 hits|program A.{0,40}\b0 hits|"
                            r"first program returned a clean null", txt, re.I)
            check(f"{label} does not call program A a zero-hit null", bad is None,
                  f"program A has {int(a.n_hits_q05)} hits: {bad.group(0) if bad else ''}")
        kr = controls[(controls.control == "known_regulator_recovery")
                      & (controls.program == "program_a")]
        check("program A's null is the known-regulator control, and it FAILs",
              len(kr) == 1 and kr.verdict.iloc[0] == "FAIL")
        check("program A's hit count is stated where the null is discussed",
              str(int(a.n_hits_q05)) in report and str(int(a.n_hits_q05)) in readme_txt,
              f"expected {int(a.n_hits_q05)} in both")

    # ---------------- K. the selection-criteria section ----------------
    # Every number in "What we chose, and why" is checkable, so check it. This
    # section exists to preempt a reviewer; if it drifts from the frozen files it
    # does the opposite.
    rd = (ROOT / "README.md").read_text()
    if "## What we chose, and why" in rd:
        sel = rd.split("## What we chose, and why")[1].split("## Findings")[0]
        lo, hi = int(summary.n_declared.min()), int(summary.n_declared.max())
        check("selection: declared-size range matches program_summary",
              f"{lo} to {hi} declared members" in sel, f"frozen {lo}-{hi}")
        check("selection: the size ratio is stated correctly",
              f"{round(hi / lo)}\u00d7 size range" in sel,
              f"frozen ratio {hi / lo:.1f}x")
        check("selection: knockdown count matches provenance",
              f"{prov['tier1']['knockdown_targets']:,} knockdowns" in sel)
        check("selection: concordance matches controls.csv",
              f"{float(gp.value.iloc[0])}" in sel.replace("\u2212", "-"))
        rc = controls[controls.control == "rpe1_coverage_collision"]
        check("selection: the RPE1 decline cites the control that justifies it",
              len(rc) == 1 and rc.verdict.iloc[0] == "FAIL"
              and "94.1% vs 11.3%" in sel, "RPE1 coverage control")
        check("selection: states what was NOT attempted",
              "did not attempt" in sel.lower())

    # ---------------- L. docs/LOOP.md describes the real code ----------------
    # LOOP.md documents criterion 1 and hands a reviewer a grep to falsify it. If
    # the doc and the code drift apart, the grep becomes the reviewer's find
    # rather than ours, so tie every claim it makes to its source.
    loop_p = ROOT / "docs" / "LOOP.md"
    if loop_p.exists():
        loop = loop_p.read_text()
        ne = (ROOT / "src" / "next_experiment.py").read_text()
        # the falsification test the doc publishes, actually run
        named = re.search(r"^\s*(?:if|elif).*(HALLMARK_|REACTOME_)", ne, re.M)
        check("LOOP.md's own falsification grep still returns nothing",
              named is None, named.group(0).strip() if named else "")
        sweep = (ROOT / "src" / "sweep.py").read_text()
        mf = re.search(r"MIN_FRAC,\s*MIN_N,\s*ALPHA\s*=\s*([\d.]+),\s*(\d+)", sweep)
        check("LOOP.md gate thresholds match src/sweep.py",
              mf is not None and f"\u2265{mf.group(1)} fraction" in loop
              and f"\u2265{mf.group(2)} present" in loop,
              f"code says {mf.groups() if mf else '?'}")
        hm = re.search(r"HIT_MIN_HITS\s*=\s*(\d+)", ne)
        check("LOOP.md hit threshold matches next_experiment.py",
              hm is not None and f"hit threshold of {hm.group(1)}" in loop,
              f"code says {hm.group(1) if hm else '?'}")
        for n, label in [(gap["gate_fail_but_has_hits"], "gate-fail-with-hits"),
                         (gap["gate_pass_but_zero_hits"], "gate-pass-zero-hits")]:
            check(f"LOOP.md states {label} as {n}", f"{n}" in loop)
        check("LOOP.md discloses that the predictor failed its own evaluation",
              f"{held['axis2_balanced_accuracy']}" in loop
              and "not refit" in loop.lower())

    # ---------------- M. no broken internal links ----------------
    # A dead link in the docs index is the cheapest possible thing for a reviewer
    # to find and the cheapest for us to prevent.
    for md in [ROOT / "README.md", ROOT / "docs" / "README.md"]:
        if not md.exists():
            continue
        broken = []
        for target in re.findall(r"\]\(([^)\s#]+)", md.read_text()):
            if target.startswith(("http://", "https://", "mailto:")):
                continue
            if not (md.parent / target).resolve().exists():
                broken.append(target)
        check(f"{md.relative_to(ROOT)} has no broken relative links",
              not broken, ", ".join(broken[:3]))

    # The positive control must never present itself as the headline. It said
    # "The headline." at the top for hours while section 4 of the same file
    # called it a recovered known answer.
    sre = ROOT / "docs" / "SREBF2_EVIDENCE.md"
    if sre.exists():
        s = sre.read_text()
        check("the control document calls itself a control, not the headline",
              "positive control, not the headline" in s
              and "not a discovery" in s.lower())

    # ---------------- N. the design system is real ----------------
    # docs/DESIGN.md documents a palette and a type scale. A design doc nobody
    # checks is decoration, so check it: every colour the page uses must be a
    # declared token, and the token values must match what the doc claims.
    design_p = ROOT / "docs" / "DESIGN.md"
    bp = (ROOT / "src" / "build_page.py").read_text()
    if design_p.exists():
        design = design_p.read_text()
        tokens = dict(re.findall(r"--([a-z]+):\s*([^;]+);", bp))
        for name in ("ink", "soft", "rule", "fill", "paper", "accent"):
            val = tokens.get(name, "").strip()
            check(f"DESIGN.md documents --{name} as the code defines it",
                  val and f"`{val}`" in design, f"code has {val!r}")
        # Allowed = the documented token TABLE (verified against code above) plus
        # the ColorBrewer figure/diagram palette. Parsing the table, not the whole
        # doc, keeps prose mentions of retired greys (e.g. #111827 in the
        # resolved-drift note) from silently re-entering the allow-set. This also
        # picks up --faint #a3a39b, which the doc declares but index.html renders
        # via the --rule alpha, so it is absent from the code :root.
        doc_tokens = dict(re.findall(r"\|\s*`--(\w+)`\s*\|\s*`([^`]+)`", design))
        allowed = {v.strip().lower() for v in doc_tokens.values()}
        allowed |= {"#b2182b", "#2166ac", "#999999", "#bbbbbb", "#888888",
                    "#444444", "#fff3e0", "#e0a458", "#d9d9d9", "#f4a582",
                    "#1a4d7a", "#eaf0f6", "#eef4ea", "#3d6b2e", "#e3e3e3"}
        css = bp.split('CSS = """')[1].split('"""')[0] if 'CSS = """' in bp else ""
        # PALETTE IS CHECKED ON EVERY RENDERED SURFACE, not just index.html.
        # app.py shipped cool Tailwind greys unseen for weeks because this block
        # read build_page's CSS alone -- the same one-surface gap that let the
        # seal framing linger on the Streamlit page. app.py adds a semantic STATUS
        # palette in chrome (tool-chain ok/warn/fail, loop null/hit/miss) on top
        # of the neutral tokens, documented in DESIGN.md.
        m = re.search(r"<style>(.*?)</style>", app_src, re.S)
        status = {"#1a7f37", "#9a6700", "#b2182b", "#2166ac"}  # app.py chrome, documented
        # Grandfathered BY NAME, not waved through: the brand pass reached
        # index.html and not app.py, which still carries the previous generation
        # of warm neutrals. Enumerating them means the exception is visible and
        # dies the moment app.py is converged -- see DESIGN.md "Known drift".
        legacy = {"#1c1c1a", "#8c8c89", "#a3a39b", "#f2f2f0"}
        STYLESHEETS = {
            "index.html": (css, allowed),                      # CSS lives in build_page
            "app.py": (m.group(1) if m else "", allowed | status | legacy),
        }
        strays = {}
        for label, (sheet, ok) in STYLESHEETS.items():
            s = sorted({h.lower() for h in re.findall(r"#[0-9a-fA-F]{6}", sheet)} - ok)
            if s:
                strays[label] = s
        check("no undocumented colour in any rendered stylesheet", not strays,
              "; ".join(f"{k}: {', '.join(v[:3])}" for k, v in strays.items()))
        # A new styled surface must join STYLESHEETS (not just the scope SURFACES),
        # and app.py's status palette must stay documented.
        styled = {s for s, src in {"index.html": page, "app.py": app_src,
                                   "results/figures/CAPTIONS.md": caps,
                                   "REPORT.md": report}.items() if "<style" in src}
        check("every styled surface is palette-registered and status palette documented",
              styled <= set(STYLESHEETS) and "#1a7f37" in design and "#9a6700" in design,
              f"styled unchecked: {sorted(styled - set(STYLESHEETS))}")
        check("DESIGN.md records the app.py palette drift rather than hiding it",
              "Known drift" in design and "#111827" in design)
        check("every grandfathered app.py colour is named in DESIGN.md",
              all(c in design.lower() for c in legacy),
              f"undocumented: {sorted(c for c in legacy if c not in design.lower())}")
        # The guard's job is that the doc and the code agree on the corner, not
        # that the corner is any particular value. Hardcoding 0px meant a
        # deliberate change to the radius read as a test failure rather than as a
        # design decision. Read the value from :root and hold the doc to it, so
        # drift still fails but a decision does not.
        m_rad = re.search(r"--radius:\s*([0-9]+px)", bp)
        check("DESIGN.md documents the radius as the code defines it",
              m_rad and f"`{m_rad.group(1)}`" in design,
              f"code has {m_rad.group(1) if m_rad else 'no --radius'}")
        # A non-zero radius must not be applied with `*`: that rounds every
        # hairline and rule on the page, which is never what is wanted.
        m_star = re.search(r"\*\{([^}]*)\}", css)
        star_has_radius = bool(m_star and "border-radius" in m_star.group(1))
        check("a non-zero radius is not applied with the universal selector",
              m_rad and (m_rad.group(1) == "0px" or not star_has_radius),
              f"radius {m_rad.group(1) if m_rad else '?'} applied via *")

    # ---------------- O. the RPE1 arm ----------------
    # The only positive result in this project that is not a control, so it gets
    # the most hostile invariants: the thresholds must match the pre-registration
    # that was committed before the run, the scorer must be untouched, and the
    # margin must be stated because it is thin.
    rp = ROOT / "results" / "rpe1" / "rpe1_evaluation.json"
    pre_p = ROOT / "docs" / "RPE1_PREREG.md"
    if rp.exists() and pre_p.exists():
        r = json.loads(rp.read_text())
        import hashlib
        live = hashlib.sha256(pre_p.read_bytes()).hexdigest()
        check("RPE1: pre-registration unchanged since the run",
              live == r["preregistration"]["sha256"], live[:16])
        check("RPE1: thresholds in the doc match the ones applied",
              "**0.25**" in pre_p.read_text() and "**0.10**" in pre_p.read_text())
        check("RPE1: the frozen scorer was not modified",
              r["scorer_sha256"].startswith("2abfdc6f") and r["scorer_unmodified"])
        check("RPE1: verdict follows its own rule",
              (r["size_alone_r2"] >= 0.25 and r["slope"] > 0)
              == (r["verdict"] == "REPRODUCES"),
              f"r2={r['size_alone_r2']} slope={r['slope']}")
        check("RPE1: scoreable count clears the pre-registered floor of 35",
              r["n_scoreable"] >= 35, f"got {r['n_scoreable']}")
        check("RPE1: the 24.3% coverage caveat travels with the result",
              "24.3%" in r["scope"] and "NOT a replication" in r["scope"])
        check("RPE1: does not revise the frozen primary",
              "does not revise" in " ".join(r).lower()
              or "does_not_revise" in r)
        check("RPE1: results are outside results/frozen/",
              not (FROZEN / "rpe1_evaluation.json").exists())

    # ---------------- P. cross-screen concordance ----------------
    cc = ROOT / "results" / "concordance" / "cross_screen.json"
    if cc.exists():
        c = json.loads(cc.read_text())
        raw = c["raw_agreement"]["spearman_rho"]
        par = c["how_much_is_size"]["spearman_after_removing_size"]
        check("concordance: removing size lowers agreement, never raises it",
              par < raw, f"raw {raw} vs partial {par}")
        check("concordance: the size-alone top-k beats chance",
              c["how_much_is_size"]["top_k_overlap_using_SIZE_ALONE_to_predict_rpe1"]["top_10"]
              > c["raw_agreement"]["top_k_overlap_expected_by_chance"]["top_10"])
        check("concordance: labelled post-freeze",
              "NOT PRE-REGISTERED" in c.get("status", ""))
        check("concordance: states its own limits",
              "not a general estimate" in c.get("limits", ""))
        # the portable tool must reproduce the bespoke analysis
        from src.audit_screen import audit_replication          # noqa: E402
        pp = pd.read_csv(ROOT / "results" / "concordance" / "paired_programs.csv")
        rep = audit_replication(pp.n_present_k562, pp.n_hits_q05_k562,
                                pp.n_hits_q05_rpe1)
        check("the portable replication auditor reproduces our own number",
              near(rep["raw_agreement_spearman"], raw, 1e-3),
              f"tool {rep['raw_agreement_spearman']} vs analysis {raw}")
        check("replication auditor refuses too few paired sets",
              _raises(audit_replication, [1, 2, 3], [1, 2, 3], [1, 2, 3]))

    # ---------------- Q. the user-facing loop actually closes ----------------
    # The page claims: audit says CONFOUNDED, you apply the correction it names,
    # you re-audit and the score drops to zero. That is the product's whole
    # argument, so run it rather than asserting it.
    import numpy as _np
    import statsmodels.api as _sm
    from src.audit_screen import audit as _audit                # noqa: E402
    _before = _audit(summary.n_present, summary.n_hits_q05)
    _y = _np.log10(1 + summary.n_hits_q05)
    _r = _sm.OLS(_y, _sm.add_constant(summary.n_present)).fit().resid
    _after = _audit(summary.n_present, (10 ** (_r - _r.min())) - 1)
    check("the correction the tool recommends actually lowers its own score",
          _after["r2_size_alone"] < _before["r2_size_alone"],
          f"{_before['r2_size_alone']} -> {_after['r2_size_alone']}")
    check("audit flags our own screen before the correction",
          _before["verdict"] == "CONFOUNDED", _before["verdict"])
    check("audit clears our own screen after the correction",
          _after["verdict"] == "NOT SIZE-DOMINATED", _after["verdict"])
    check("the page states the before/after the test just reproduced",
          f"{_before['r2_size_alone']}" in page and "NOT SIZE-DOMINATED" in page)
    # the connect snippet must name a module that exists and is runnable
    check("the MCP snippet on the page points at a real module",
          '"-m", "src.mcp_server"' in page
          and (ROOT / "src" / "mcp_server.py").exists())

    # ---------------- R. the server refuses to be misused ----------------
    # The scope guard stops US publishing a gene-level claim; it does nothing
    # when an agent calls the server. Prior art: CRISPR-GPT hard-codes
    # non-bypassable refusals rather than trusting the model to be careful.
    from src.answers import refuse as _refuse                   # noqa: E402
    for q in ("SREBF2", "TP53", "MYC"):
        r = _refuse(q)
        check(f"server refuses the bare gene symbol {q}",
              r is not None and r["status"] == "REFUSED")
    for q in ("top 10 candidates", "which gene should I chase",
              "rank the programs", "most promising target"):
        r = _refuse(q)
        check(f"server refuses a nomination request: {q!r}",
              r is not None and r["status"] == "REFUSED")
    for q in ("HALLMARK_CHOLESTEROL_HOMEOSTASIS",
              "REACTOME_SCAVENGING_OF_HEME_FROM_PLASMA"):
        check(f"server still answers a real program: {q[:28]}",
              _refuse(q) is None)
    check("the refusal explains itself with the concordance figure",
          str(float(gp.value.iloc[0])) in _refuse("SREBF2")["reason"])
    check("the nomination refusal cites the predictor's own failure",
          str(held["axis2_balanced_accuracy"]) in _refuse("top hits")["reason"])

    # ---------------- R1. no git-tracked symlinks into an absolute path -------
    # A worktree linked data/raw at the primary tree to share the git-ignored
    # substrate. `.gitignore` said `data/raw/` -- with a trailing slash, which
    # ignores a DIRECTORY of that name and not a SYMLINK of that name -- so
    # `git add -A` committed the link. Every checkout after that materialised
    # data/raw as a symlink pointing at itself: not a broken share, a directory
    # that hides the substrate and cannot be written into. A clean clone got it
    # too. Cheap to assert, expensive to rediscover.
    import subprocess as _sp
    _tracked = _sp.run(["git", "ls-files", "-s"], cwd=ROOT, capture_output=True,
                       text=True).stdout.splitlines()
    _links = [ln.split("\t", 1)[1] for ln in _tracked if ln.startswith("120000")]
    _abs_links = []
    for _p in _links:
        try:
            _t = (ROOT / _p).readlink()
        except OSError:                                       # pragma: no cover
            continue
        if _t.is_absolute():
            _abs_links.append(f"{_p} -> {_t}")
    check("no tracked symlink points at an absolute path",
          not _abs_links, "; ".join(_abs_links))
    check("data/raw is not tracked at all", "data/raw" not in _links)
    check("data/raw is ignored as a name, not only as a directory",
          "\ndata/raw\n" in (ROOT / ".gitignore").read_text())

    # ---------------- R2. the server serves the PRODUCT, not just the study ----
    # `reversibility` and `provenance` are lookups into our frozen result: an
    # agent could ask what WE found and could not run the check on anything of
    # its own. `audit` and `rerank` are the packaged tool, so the server is now
    # the instrument as well as the database. These assert that they are the
    # PACKAGED functions -- a server-side reimplementation would be item 1's
    # duplication all over again, one layer out.
    import src.mcp_server as _srv                               # noqa: E402
    check("the server exposes all four tools",
          all(hasattr(_srv, t) for t in
              ("reversibility", "provenance", "audit", "rerank")))
    check("the server's audit IS the packaged audit",
          _srv._audit is _pkg_core.audit)
    check("the server's rerank IS the packaged rerank",
          _srv._rerank is _pkg_core.rerank)

    # The point of these two is that they answer about the CALLER's data. Run
    # them on numbers that have nothing to do with this screen and check the
    # answer is a property of those numbers.
    _sz = [10, 20, 40, 80, 160, 320, 25, 55, 90, 200]
    _ht = [1, 3, 6, 12, 25, 60, 4, 9, 15, 33]
    _a = _srv.audit(sizes=_sz, hits=_ht)
    check("server audits a caller's own ranking, no frozen data involved",
          _a["verdict"] == "CONFOUNDED" and _a["n_sets"] == 10,
          f"r2={_a['r2_size_alone']}")
    _r = _srv.rerank(sizes=_sz, hits=_ht, top=5)
    check("server reranks a caller's own ranking",
          _r["top_n"] == 5 and 0 <= _r["survived_top_n"] <= 5)
    # Constant size must not be reported as an all-clear through the server
    # either -- that is the branch a MAGeCK/BAGEL/drugZ caller lands on.
    check("server reports UNDETERMINED rather than clearing a constant-size input",
          _srv.audit(sizes=[50] * 10,
                     hits=[1, 4, 2, 9, 3, 7, 5, 6, 8, 2])["verdict"] == "UNDETERMINED")
    # An MCP client renders a returned dict and buries a traceback, so bad input
    # must come back as a value.
    for _bad, _lbl in ((dict(sizes=[1, 2, 3], hits=[1, 2, 3]), "too few sets"),
                       (dict(), "neither arrays nor a path"),
                       (dict(table_path="/nonexistent/nope.csv"), "missing file")):
        check(f"server returns an error value, not a traceback: {_lbl}",
              _srv.audit(**_bad).get("status") == "ERROR")

    # The path route is the one an agent actually uses: point at the file your
    # enrichment tool already wrote. Through it, our own g:Profiler-shaped export
    # must return the two numbers the page publishes.
    _ex = ROOT / "examples" / "example_gprofiler.csv"
    _pa = _srv.audit(table_path=str(_ex))
    _pr = _srv.rerank(table_path=str(_ex), top=10)
    check("server's audit on our own export reproduces the published R2",
          near(_pa["r2_size_alone"], 0.4649, 5e-3), f"{_pa['r2_size_alone']}")
    check("server's rerank on our own export reproduces the published 3 of 10",
          _pr["survived_top_n"] == 3, f"{_pr['survived_top_n']}")
    check("server names the format it read the caller's table as",
          _pa.get("input_format") == "g:Profiler", _pa.get("input_format"))

    # The asymmetry is the design and the README has to carry it, because a
    # server that applies a correction while refusing to nominate is unusual
    # enough that a reader will otherwise read it as an oversight.
    _rdme = (ROOT / "README.md").read_text()
    check("README states the four tools and the two halves",
          "Four tools in two halves" in _rdme)
    check("README states the apply-but-never-nominate asymmetry",
          "deliberately asymmetric" in _rdme and "will not nominate" in _rdme)
    check("the asymmetry is justified by the predictor's own failure",
          str(held["axis2_balanced_accuracy"]) in _rdme)

    # ---------------- R3. the benchmark task built on the PRODUCT -------------
    # denali-gate-trap and denali-confound-estimate score a FINDING: can you
    # reproduce what we measured. denali-size-carried scores the product: can you
    # apply the correction the tool ships. Its answer key is therefore not a
    # transcription of anything -- it is re-derived here from the packaged
    # rerank() and must match the committed key exactly, so a change to the tool
    # either updates the benchmark or fails the build.
    import numpy as np                                          # noqa: E402
    _sc = ROOT / "benchmarks" / "tasks" / "denali-size-carried"
    _key = json.loads((_sc / "verifier" / "answer_key.json").read_text())
    _ranked = json.loads((_sc / "environment" / "data" / "ranked_top10.json").read_text())
    check("the size-carried task has all seven screens keyed",
          len(_key) == 7 and set(_key) == set(_ranked), f"{sorted(_key)}")

    _tp = _fp = _tn = _fn = 0
    _all_true, _all_pred_big = [], []
    for _s in sorted(_key):
        _d = pd.read_csv(_sc / "environment" / "data" / f"{_s}.csv")
        _rr = _pkg_core.rerank(_d["size"], _d["hits"], _d["set"], top=10)
        # Re-derive size-carried by RANK, the way the verifier grades it.
        _y = np.log10(1.0 + _d["hits"].values.astype(float))
        _sz = _d["size"].values.astype(float)
        _b = np.polyfit(_sz, _y, 1)
        _res = _y - np.polyval(_b, _sz)
        _crank = (-_res).argsort(kind="stable").argsort(kind="stable") + 1
        _derived = sorted(e["rank"] for e in _ranked[_s] if _crank[e["row"]] > 10)
        check(f"size-carried key re-derives from the packaged rerank: {_s}",
              _derived == sorted(_key[_s]["size_carried_ranks"]),
              f"derived {_derived} vs key {_key[_s]['size_carried_ranks']}")
        check(f"size-carried key agrees with rerank's own survivor count: {_s}",
              len(_derived) == _rr["left_top_n"] == 10 - _key[_s]["survived_top_n"],
              f"{len(_derived)} vs {_rr['left_top_n']}")
        # the pinned ranking must be the real top 10 by hits, in order
        check(f"the pinned top 10 is the actual hit ranking: {_s}",
              [e["hits"] for e in _ranked[_s]]
              == sorted((e["hits"] for e in _ranked[_s]), reverse=True))
        check(f"pinned rows point at the entries they claim: {_s}",
              all(int(_d["hits"].values[e["row"]]) == e["hits"]
                  and int(_d["size"].values[e["row"]]) == e["size"]
                  for e in _ranked[_s]))
        _t = set(_key[_s]["size_carried_ranks"])
        _all_true.append((_s, _t))
        _big = {e["rank"] for e in sorted(_ranked[_s], key=lambda e: -e["size"])[:7]}
        _all_pred_big.append((_s, _big))

    _n_carried = sum(len(t) for _, t in _all_true)
    check("the size-carried task is 47 of 70 decisions, as documented",
          _n_carried == 47 and 10 * len(_key) == 70, f"{_n_carried}/70")

    def _bal(pred_by_screen):
        tp = fp = tn = fn = 0
        for (s, t), (_s2, p) in zip(_all_true, pred_by_screen):
            tp += len(p & t); fp += len(p - t); fn += len(t - p)
            tn += 10 - len(p & t) - len(p - t) - len(t - p)
        sens = tp / (tp + fn) if tp + fn else 0.0
        spec = tn / (tn + fp) if tn + fp else 0.0
        return 0.5 * (sens + spec)

    # The zero point is the whole design: BOTH constants must score exactly 0.5,
    # so the shortcut "everything is carried" earns nothing. This is arithmetic,
    # not a tuned baseline, and asserting it stops a future metric change from
    # quietly making the shortcut pay.
    _all_yes = [(s, set(range(1, 11))) for s, _ in _all_true]
    _all_no = [(s, set()) for s, _ in _all_true]
    check("size-carried: calling everything carried scores exactly 0.5",
          abs(_bal(_all_yes) - 0.5) < 1e-12, f"{_bal(_all_yes)}")
    check("size-carried: calling nothing carried scores exactly 0.5",
          abs(_bal(_all_no) - 0.5) < 1e-12, f"{_bal(_all_no)}")
    check("size-carried: the oracle's answer scores 1.0",
          abs(_bal(_all_true) - 1.0) < 1e-12, f"{_bal(_all_true)}")
    # And the documented naive baseline is re-derived, not transcribed.
    _big_bal = _bal(_all_pred_big)
    _bench_md = (ROOT / "benchmarks" / "README.md").read_text()
    _task_md = (_sc / "task.md").read_text()
    check("size-carried: the largest-70% baseline is the documented 0.7623",
          near(_big_bal, 0.7623, 5e-5), f"{_big_bal:.4f}")
    for _doc, _lbl in ((_bench_md, "benchmarks/README.md"), (_task_md, "task.md")):
        check(f"{_lbl} states the re-derived 0.7623 baseline",
              f"{_big_bal:.4f}" in _doc)
        check(f"{_lbl} states the {max(0.0, 2 * _big_bal - 1):.4f} reward it earns",
              f"{max(0.0, 2 * _big_bal - 1):.4f}" in _doc)
    check("the size-carried task grades in code, with no model judging it",
          not (_sc / "verifier" / "rubrics").exists()
          and "No model judges" in _task_md)
    check("the size-carried task names no gene",
          "No gene is named in this task" in _task_md)
    check("benchmarks/README says three tasks, two findings and one product",
          "Three BenchFlow tasks" in _bench_md and "turns the\n**product**" in _bench_md)

    # ---------------- S. every branch says what would demote it ----------------
    # A proposal that cannot be wrong is not a proposal. The hit branch had no
    # falsification condition for hours, which is backwards -- that is the branch
    # where someone commits a year.
    from src.next_experiment import propose as _prop            # noqa: E402
    seen_outcomes = set()
    for prog in summary.program:
        pr = _prop(prog, summary)
        seen_outcomes.add(pr["outcome"])
        cmm = pr.get("what_would_change_my_mind", "")
        check(f"{pr['outcome']}: states what would change its mind",
              bool(cmm) and len(cmm) > 40, f"{prog}: {cmm[:40]!r}")
        if pr["outcome"] == "HIT_ABOVE_THRESHOLD":
            check(f"hit branch names a numeric threshold that would demote it",
                  "residual" in cmm and any(ch.isdigit() for ch in cmm))
        break_after = len(seen_outcomes) >= 3
        if break_after:
            break
    check("all three real branches were exercised",
          {"HIT_ABOVE_THRESHOLD", "NULL_WITH_MECHANISM", "WEAK"} <= seen_outcomes)
    check("the falsification panel reaches the page",
          '"change_my_mind"' in page and "What would change my mind" in page)

    # ---------------- T. the annotation arm, incl. its own failure ----------------
    ap_ = ROOT / "results" / "annotation" / "annotation_evaluation.json"
    apre = ROOT / "docs" / "ANNOTATION_PREREG.md"
    if ap_.exists() and apre.exists():
        an = json.loads(ap_.read_text())
        import hashlib
        live = hashlib.sha256(apre.read_bytes()).hexdigest()
        check("annotation: pre-registration unchanged since the run",
              live == an["preregistration"]["sha256"], live[:16])
        check("annotation: the frozen scorer was not modified",
              an["scorer_sha256"].startswith("2abfdc6f"))
        po = an["preregistered_outcome"]
        check("annotation: the power rule fired and no verdict was issued",
              "UNDERPOWERED" in po["verdict"] and "NO VERDICT" in po["verdict"])
        check("annotation: says plainly that our prediction was wrong in direction",
              "wrong in direction" in po["what_the_numbers_would_have_shown"])
        d = an["descriptive_not_preregistered"]["per_collection"]
        check("annotation: scoreability falls from Hallmark to GO-BP",
              d["hallmark"]["scoreable_fraction"] > d["go_bp"]["scoreable_fraction"],
              f"{d['hallmark']['scoreable_fraction']} vs {d['go_bp']['scoreable_fraction']}")
        check("annotation: the descriptive finding is labelled not pre-registered",
              "no threshold was set for it" in
              an["descriptive_not_preregistered"]["finding"])
        # the Hallmark bar reconciliation: our own baseline appears to fail its
        # own bar, and the artifact must keep explaining why. Recompute BOTH.
        rec = an["hallmark_bar_reconciliation"]
        _sc = pd.read_csv(ROOT / "results" / "annotation" / "sets_scored.csv")
        _hk = _sc[(_sc.collection == "hallmark") & _sc.scoreable]
        import statsmodels.api as _sm2
        _r50 = float(_sm2.OLS(summary.R_p,
                              _sm2.add_constant(summary.n_present)).fit().rsquared)
        _r49 = float(_sm2.OLS(_hk.R_p, _sm2.add_constant(_hk.n_present)).fit().rsquared)
        check("hallmark reconciliation: the all-50 value recomputes",
              near(rec["r2_frozen_all_50"], _r50), f"{rec['r2_frozen_all_50']} vs {_r50:.4f}")
        check("hallmark reconciliation: the 49-set value recomputes",
              near(rec["r2_arm_49_scoreable"], _r49), f"{rec['r2_arm_49_scoreable']} vs {_r49:.4f}")
        check("hallmark reconciliation: the delta is the difference of the two",
              near(rec["delta"], _r50 - _r49), f"{rec['delta']} vs {_r50 - _r49:.4f}")
        check("hallmark reconciliation: attributed to sample size, not drift",
              "not drift" in rec["cause"])
        check("hallmark is labelled the baseline, not a failing candidate",
              an["per_collection"]["hallmark"].get("is_the_baseline_not_a_candidate")
              is True
              and "exceeds_hallmark_bar" not in an["per_collection"]["hallmark"])
        check("the direction claim is asserted under BOTH bars",
              "0.4464 and at 0.4649" in rec["does_the_direction_claim_survive"])
        check("the bar's post-freeze provenance is disclosed",
              "NOT PRE-REGISTERED" in rec["provenance_of_the_0_4649_bar"])

        # the two medians must come from the SAME subset. Pairing declared-over-all
        # with measured-over-scoreable produced "20 declared, 30 measured" for
        # GO-BP, which is impossible and shipped to the page for a few minutes.
        _raw = pd.read_csv(ROOT / "results" / "annotation" / "sets_scored.csv")
        for _c, _v in d.items():
            _sub = _raw[_raw.collection == _c]
            check(f"annotation: {_c} medians are both over all sampled sets",
                  _v["median_genes_declared"] == int(_sub.n_declared.median())
                  and _v["median_genes_measured_in_screen"] == int(_sub.n_present.median()),
                  f"json {_v['median_genes_declared']}/{_v['median_genes_measured_in_screen']}")
            check(f"annotation: {_c} cannot measure more genes than it declares",
                  _v["median_genes_measured_in_screen"] <= _v["median_genes_declared"],
                  f"{_v['median_genes_measured_in_screen']} > {_v['median_genes_declared']}")

        # recompute the headline descriptive number from the raw scored table
        sc = pd.read_csv(ROOT / "results" / "annotation" / "sets_scored.csv")
        g = sc[sc.collection == "go_bp"]
        check("annotation: the GO-BP scoreable fraction recomputes from raw",
              near(g.scoreable.sum() / len(g), d["go_bp"]["scoreable_fraction"], 2e-3))

    # ---------------- F. the docs' own self-description ----------------
    report_readme = (ROOT / "README.md").read_text()

    # -- F0. PROSE DRIFT. Numbers were guarded; sentences were not, and that is
    # exactly how three self-contradictions reached the first screen a reader
    # sees: "Six evaluations ... Three did come back negative" sat two paragraphs
    # above a seven-row findings table, "Four of our six evaluations" repeated it
    # 300 lines later, and the traced-value count said 32 in one place and 47 in
    # another. Seven further copies were stale in CLAUDE.md, the docs and the
    # spoken demo script. A number that only lives in a sentence drifts silently.
    #
    # The findings table in README.md is the ONLY source of truth for how many
    # evaluations exist and how many were negative; src/build_page.py's own TRACE
    # is the only source of truth for how many values are traced. Every prose
    # restatement of either is checked against its source, so rewording a claim
    # without rewording its siblings fails the build.
    rows = re.findall(r"^\|\s*(\d+)\s*\|.*\|\s*\*\*([A-Z][A-Z ]+)\*\*",
                      report_readme, re.M)
    n_eval = len(rows)
    n_neg = [v.strip() for _, v in rows].count("NEGATIVE")
    check("README findings table is numbered 1..n with one verdict each",
          n_eval >= 4 and [int(i) for i, _ in rows] == list(range(1, n_eval + 1)),
          f"parsed {[i for i, _ in rows]}")

    from src.build_page import TRACE                              # noqa: E402
    n_traced = len(TRACE)
    check("build_page traces at least one value per frozen source", n_traced > 0)

    _WORDS = {1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six",
              7: "seven", 8: "eight", 9: "nine", 10: "ten", 11: "eleven",
              12: "twelve"}

    def _count(tok: str) -> int:
        """'Seven' | 'seven' | '7' -> 7.  -1 if the token is not a count."""
        t = tok.strip().lower()
        return int(t) if t.isdigit() else next(
            (k for k, v in _WORDS.items() if v == t), -1)

    # How many negative findings the page actually sets out as cards. The
    # heading has to agree with this, not with a number someone typed once.
    _neg_sec = re.search(r"<h2[^>]*>\w+ of the \w+ negative findings</h2>.*?</section>",
                         page, re.S)
    n_neg_cards = len(re.findall(r'<div class="card">', _neg_sec.group(0))) \
        if _neg_sec else -1

    # (file, pattern, expected group values in order, what the sentence is)
    prose_claims = [
        ("README.md", r"(\w+) evaluations\. (\w+) negative,",
         (n_eval, n_neg), "the findings header"),
        ("README.md", r"\*\*(\w+) evaluations, (\w+) of them negative\.\*\*",
         (n_eval, n_neg), "the what-we-chose list"),
        ("README.md", r"\*\*(\w+) of our (\w+) evaluations came back negative\.\*\*"
                      r" All (\w+) are reported",
         (n_neg, n_eval, n_eval), "the not-fooling-ourselves list"),
        ("CLAUDE.md", r"\*\*(\w+) evaluations\. (\w+) negative\. All (\w+) reported\.\*\*",
         (n_eval, n_neg, n_eval), "the operational contract"),
        ("docs/METHOD_RULES.md",
         r"(\w+) of (\w+) evaluations here are negative and all (\w+)\s+are reported",
         (n_neg, n_eval, n_eval), "the preserve-negatives rule"),
        ("docs/ORIGINS.md",
         r"(\w+) of this project's (\w+) evaluations came\s+back negative and all (\w+) are reported",
         (n_neg, n_eval, n_eval), "the negatives-kept note"),
        ("docs/MORNING_HANDOFF.md",
         r"(\w+) evaluations were run, (\w+) came back negative, and all (\w+) are\s+reported",
         (n_eval, n_neg, n_eval), "the handoff summary"),
        ("docs/MORNING_HANDOFF.md", r"##\s*2\.\s*The (\w+) results",
         (n_eval,), "the handoff results heading"),
        ("docs/DEMO.md", r"The repeated number is (\w+) OF (\w+)\.",
         (n_neg, n_eval), "the demo motif"),
        ("docs/DEMO.md",
         r"We ran (\w+) evaluations on this project\. (\w+) of them came back negative\.",
         (n_eval, n_neg), "the demo open"),
        ("docs/DEMO.md", r"(\w+) of (\w+) evaluations negative\.",
         (n_neg, n_eval), "the demo close"),
        # Now states BOTH counts. "Seven evaluations came back negative" was
        # correct English for seven negatives but read as a total to anyone
        # skimming, and the cross-surface guard flagged it as a disagreement
        # with the eleven every other surface states. Naming both numbers is
        # unambiguous and gives this check two things to hold.
        ("app.py",
         r'st\.subheader\("(\w+) of (\w+) evaluations came back negative"\)',
         (n_neg, n_eval), "the streamlit negatives heading"),
        # index.html was the one rendered surface this registry never named, and
        # it drifted exactly the way app.py did before it was added: the page
        # still said "4 evaluations / 3 came back negative / The three negative
        # findings" for three arms after the count reached 7 and 4. The tally and
        # the heading are hand-typed, so they are checked against the same source
        # every other surface is checked against.
        # The tally became one sentence in 60fd349, so these now read the lede
        # rather than the stat tiles -- same intent, current markup. Keeping the
        # old selectors would have failed loudly, which is right, but pointing
        # them at markup that no longer exists teaches nothing.
        ("index.html", r'class="lede">(\w+) evaluations\.',
         (n_eval,), "the page lede, evaluation count"),
        ("index.html", r'class="lede">\w+ evaluations\. (\w+) came back negative',
         (n_neg,), "the page lede, negative count"),
        # "Three of the four negative findings" — the first number is how many
        # cards that section actually renders, the second is the true total.
        # `<h2[^>]*>` and not `<h2>`: adding an anchor id to the heading broke
        # this once. The check is about the two counts, not about whether the
        # tag carries attributes.
        ("index.html", r"<h2[^>]*>(\w+) of the (\w+) negative findings</h2>",
         (n_neg_cards, n_neg), "the negatives heading"),
        # The objection-handling line in the demo. It sat at "Three of four" for
        # three arms -- through 8, 9 and 10 -- because it phrases the tally as
        # advice to the speaker rather than as a claim, so no pattern here
        # matched it. A count is a count wherever it is said out loud.
        ("docs/DEMO.md", r'"(\w+) of (\w+) came back negative" defuses it',
         (n_neg, n_eval), "the demo objection-handling line"),
        ("README.md", r"(\d+) values pass through a `V\(\)` helper",
         (n_traced,), "the traced-value feature bullet"),
        ("README.md", r"\*\*(\d+)\*\* values are traced",
         (n_traced,), "the inspectability criterion"),
        ("docs/DESIGN.md", r"`V\(\)` in `src/build_page\.py`, (\d+) values",
         (n_traced,), "the design contract table"),
    ]
    for rel, pat, expect, what in prose_claims:
        m = re.search(pat, (ROOT / rel).read_text())
        got = tuple(_count(g) for g in m.groups()) if m else None
        check(f"prose agrees with the source: {rel} — {what}",
              got == tuple(expect),
              f"expected {tuple(expect)}, got {got}" if m
              else "phrase not found — prose was reworded without updating this check")

    # ---------------- G. the corpus arm (evaluation 8, post-hoc) ----------------
    # Every number quoted from the ORCS corpus recomputes from the committed
    # per-screen table, the same discipline as results/frozen/. The raw
    # substrate (752 MB) is gitignored; docs/CORPUS.md documents the download.
    corp = json.loads((ROOT / "results" / "corpus" / "corpus_audit.json").read_text())
    per = pd.read_csv(ROOT / "results" / "corpus" / "corpus_per_screen.csv")

    check("corpus: audited count matches the per-screen table and the accounting closes",
          corp["n_screens_audited"] == len(per)
          and corp["n_screen_files"]
              == corp["n_parse_failed"] + corp["n_excluded_by_rule"] + len(per),
          f"{corp['n_screen_files']} files = {corp['n_parse_failed']} unparseable "
          f"+ {corp['n_excluded_by_rule']} excluded + {len(per)} audited")
    check("corpus: every audited screen satisfies the stated inclusion rule",
          bool((per.n_hits >= 20).all() and (per.n_measured >= 10000).all()
               and (per.n_sets_used >= 8).all()))

    c_med = float(per.r2_size_alone.median())
    check("corpus: the median recomputes from the per-screen table",
          near(c_med, corp["quantiles"]["p50"]) and near(c_med, 0.2244),
          f"recomputed {c_med:.4f}")
    c_pct = 100 * float((per.r2_size_alone >= 0.465).mean())
    check("corpus: the 9.6% figure recomputes from the per-screen table",
          near(c_pct, corp["pct_at_or_above_denali_0465"], 0.05)
          and near(c_pct, 9.6, 0.05), f"recomputed {c_pct:.1f}%")

    c_bins = [(20, 100), (100, 500), (500, 2000), (2000, 10**9)]
    c_meds = [float(per[(per.n_hits >= lo) & (per.n_hits < hi)].r2_size_alone.median())
              for lo, hi in c_bins]
    frozen_strat = [s["median_r2"] for s in corp["stratified_by_hitlist_size"]]
    check("corpus: all four hit-list-size strata recompute",
          len(frozen_strat) == 4
          and all(near(a, b) for a, b in zip(c_meds, frozen_strat)),
          f"recomputed {[round(m, 4) for m in c_meds]}")
    check("corpus: the gradient across hit-list-size bins is monotonic",
          all(a < b for a, b in zip(c_meds, c_meds[1:])),
          " -> ".join(f"{m:.3f}" for m in c_meds))

    # Pseudo-replication. 1,272 screens come from far fewer publications and one
    # of them is a quarter of the corpus, so the screen-level share and the
    # publication-level share differ by nearly 3x. The screen-level figure is the
    # flattering one, so the correction must recompute and must never be the only
    # number quoted -- if it is ever dropped, the arm overstates how atypical
    # denali is and the build should fail rather than allow it.
    cpub = corp.get("publication_level_pseudo_replication")
    check("corpus: the pseudo-replication correction survives", cpub is not None)
    if cpub:
        g = per.groupby("source_id").size()
        check("corpus: the publication count recomputes from the per-screen table",
              len(g) == cpub["n_publications"],
              f"recomputed {len(g)} vs {cpub['n_publications']}")
        check("corpus: the publication-level median recomputes",
              near(per.groupby("source_id").r2_size_alone.median().median(),
                   cpub["median"]),
              f"recomputed "
              f"{per.groupby('source_id').r2_size_alone.median().median():.4f}")
        check("corpus: the publication-level 0.465 share recomputes",
              near(100 * (per.groupby("source_id").r2_size_alone.median()
                          >= 0.465).mean(), cpub["pct_at_or_above_denali_0465"], 0.05),
              f"json {cpub['pct_at_or_above_denali_0465']}%")
        check("corpus: the corpus is disclosed as concentrated, not balanced",
              near(100 * g.max() / len(per), cpub["largest_publication_share_pct"], 0.05)
              and cpub["largest_publication_share_pct"] > 10,
              f"largest publication is {100*g.max()/len(per):.1f}% of the corpus")

    corpus_md = (ROOT / "docs" / "CORPUS.md").read_text()
    # Find this arm's row by CONTENT, not by number. It was written as row 8,
    # collided with the off-target arm's 8, and became 10 on merge -- and a
    # number-matched search does not fail when that happens, it silently starts
    # asserting against a different arm's row.
    row8 = re.search(r"^\|\s*\d+\s*\|[^|]*headline describe the field.*$",
                     report_readme, re.M)
    check("corpus: the findings row is present and found by content",
          row8 is not None,
          "no row asks whether the headline describes the field")
    if cpub:
        check("corpus: the doc reports BOTH shares, never the flattering one alone",
              f"{corp['pct_at_or_above_denali_0465']}%" in corpus_md
              and f"{cpub['pct_at_or_above_denali_0465']}%" in corpus_md,
              f"screen {corp['pct_at_or_above_denali_0465']}% / "
              f"publication {cpub['pct_at_or_above_denali_0465']}%")
        check("corpus: the doc states the publication count",
              str(cpub["n_publications"]) in corpus_md)
    check("corpus: labelled post-hoc, not pre-registered, in the doc and the findings row",
          "not pre-registered" in corpus_md.lower()
          and row8 is not None and "post-hoc" in row8.group(0).lower())
    check("corpus: the estimand warning survives in both surfaces",
          "estimand" in corpus_md.lower()
          and row8 is not None and "not the same estimand" in
          report_readme[row8.start():row8.start() + 6000].lower())
    check("corpus: the README corpus row quotes the numbers the table recomputes",
          row8 is not None and all(s in row8.group(0)
                                   for s in ("0.224", "9.6%", "1,272")))
    # The unreconciled independent run is the other load-bearing caveat in this
    # arm and it was guarded by nothing: another execution of the same idea got
    # a median near 0.10 over ~1,673 screens and the two could not be made to
    # agree. Without it the doc reads as though 0.224 were settled. It sat in
    # prose only, which is how the demo's "three of four" survived three arms.
    _dis_doc = all(s in corpus_md for s in ("0.10", "1,673")) and \
        "reconcil" in corpus_md.lower()
    _row_txt = report_readme[row8.start():row8.start() + 6000] if row8 else ""
    _dis_row = "0.10" in _row_txt and "reconcil" in _row_txt.lower()
    check("corpus: the unreconciled independent run (~0.10) is disclosed in both surfaces",
          _dis_doc and _dis_row, f"doc={_dis_doc} readme={_dis_row}")

    # Scope, the same pattern as the gene-symbol guard: the unit of inference
    # is the distribution, so no screen and no publication may be named in the
    # prose surfaces. Screen ids are small integers and would collide with
    # innocent counts, so the guard covers the two forms a real citation would
    # take: an explicit SCREEN_<id> token, or a PubMed id (source_id, >=5
    # digits — small-integer counts like "418 publications" stay legal).
    corpus_surfaces = {"docs/CORPUS.md": corpus_md,
                       "the README corpus row": row8.group(0) if row8 else ""}
    pmids = {s for s in per.source_id.dropna().astype(str) if len(s) >= 5}
    for label, text in corpus_surfaces.items():
        named = [p for p in pmids
                 if re.search(rf"(?<![\d.]){re.escape(p)}(?![\d.])", text)]
        screen_tok = re.findall(r"SCREEN[_ ]?\d+", text)
        check(f"corpus scope: no screen or publication named in {label}",
              not named and not screen_tok,
              f"found {(named + screen_tok)[:5]}" if named or screen_tok else "")

    # ---------------- H. the corpus rerank arm (post-hoc) ----------------
    # Evaluation 10 measured how much of each published ranking size explains.
    # This arm applies the packaged correction to the same screens and counts
    # what leaves the top ten. It is guarded the same way: every number quoted
    # recomputes from the committed per-screen table, and the arm's own join to
    # evaluation 10 is asserted here rather than trusted, because a silent join
    # drift would leave a plausible distribution computed over the wrong screens.
    rr_dir = ROOT / "results" / "corpus_rerank"
    rrj = json.loads((rr_dir / "corpus_rerank.json").read_text())
    rper = pd.read_csv(rr_dir / "corpus_rerank_per_screen.csv", dtype={"screen_id": str})
    rr_md = (rr_dir / "README.md").read_text()

    check("corpus rerank: audited count matches the per-screen table "
          "and the accounting closes",
          rrj["n_screens_audited"] == len(rper)
          and rrj["n_screen_files"]
              == rrj["n_parse_failed"] + rrj["n_excluded_by_rule"] + len(rper),
          f"{rrj['n_screen_files']} files = {rrj['n_parse_failed']} unparseable "
          f"+ {rrj['n_excluded_by_rule']} excluded + {len(rper)} audited")
    # The join to evaluation 10 IS the sanity check the arm rests on. Same screens,
    # same R2 values, or the distribution describes something else entirely.
    # The committed evaluation 10 table reads screen_id as an integer and this
    # one as a string; comparing them as-is silently finds zero overlap.
    per_ids = set(per.screen_id.astype(str))
    rper["screen_id"] = rper.screen_id.astype(str)
    check("corpus rerank: the screen set is evaluation 10's, exactly",
          set(rper.screen_id) == per_ids and len(rper) == len(per),
          f"rerank {len(rper)} vs corpus {len(per)}; "
          f"symmetric difference {len(set(rper.screen_id) ^ per_ids)}")
    _j = rper.merge(per.assign(screen_id=per.screen_id.astype(str)),
                    on="screen_id", suffixes=("", "_c"))
    _dr2 = float((_j.r2_size_alone - _j.r2_size_alone_c).abs().max())
    check("corpus rerank: size-alone R2 agrees with evaluation 10 screen by screen",
          _dr2 <= 1e-6, f"max |dR2| = {_dr2}")

    rq = rper.survivors_top10.quantile([0.10, 0.25, 0.50, 0.75, 0.90])
    check("corpus rerank: all five quantiles recompute from the per-screen table",
          all(near(float(v), rrj["quantiles"][f"p{int(k * 100)}"], 0.005)
              for k, v in rq.items()),
          " ".join(f"p{int(k*100)}={v:g}" for k, v in rq.items()))
    r_med = float(rper.survivors_top10.median())
    check("corpus rerank: the headline median is nine and recomputes",
          near(r_med, rrj["quantiles"]["p50"], 0.005) and near(r_med, 9.0, 0.005),
          f"recomputed {r_med:g}")
    check("corpus rerank: the zero-survivor and all-ten counts recompute",
          int((rper.survivors_top10 == 0).sum()) == rrj["n_zero_survivors"]
          and int((rper.survivors_top10 == 10).sum()) == rrj["n_all_ten_hold"],
          f"recomputed zero={int((rper.survivors_top10 == 0).sum())} "
          f"all-ten={int((rper.survivors_top10 == 10).sum())}")
    check("corpus rerank: survivor counts stay inside 0..10",
          bool(rper.survivors_top10.between(0, 10).all()),
          f"range {rper.survivors_top10.min()}-{rper.survivors_top10.max()}")

    r_meds = [float(rper[(rper.n_hits >= lo) & (rper.n_hits < hi)]
                    .survivors_top10.median()) for lo, hi in c_bins]
    check("corpus rerank: all four hit-list-size strata recompute",
          len(rrj["stratified_by_hitlist_size"]) == 4
          and all(near(a, s["median_survivors"], 0.005)
                  for a, s in zip(r_meds, rrj["stratified_by_hitlist_size"])),
          f"recomputed {r_meds}")
    # Evaluation 10's R2 gradient is monotonic; this arm's survivor "gradient" is
    # not the same quantity and mostly reflects tie density. The doc says so, and
    # the check exists so nobody later quietly promotes it to a finding.
    _rr_flat = " ".join(rr_md.split())
    check("corpus rerank: the doc refuses to read the strata as a gradient",
          "does **not** reappear as a survivor gradient" in _rr_flat,
          "the doc must say evaluation 10's gradient does not reappear here")
    check("corpus rerank: the tie sensitivity is disclosed and recomputes",
          near(100 * float(rper.top10_boundary_tied.mean()),
               rrj["tie_sensitivity"]["pct_screens_with_tied_top10_boundary"], 0.05)
          and near(float(rper[~rper.top10_boundary_tied].survivors_top10.median()),
                   rrj["tie_sensitivity"]["median_survivors_untied_screens_only"],
                   0.005),
          f"tied boundary in "
          f"{100 * float(rper.top10_boundary_tied.mean()):.1f}% of screens")

    rpub = rper.groupby("source_id").survivors_top10.median()
    rrpub = rrj["publication_level_pseudo_replication"]
    check("corpus rerank: the pseudo-replication correction survives",
          rrpub is not None and len(rpub) == rrpub["n_publications"],
          f"recomputed {len(rpub)} publications")
    check("corpus rerank: the publication-level median recomputes and is lower",
          near(float(rpub.median()), rrpub["median"], 0.005)
          and rrpub["median"] < rrj["quantiles"]["p50"],
          f"publication {float(rpub.median()):g} vs screen {r_med:g}")
    check("corpus rerank: the doc reports BOTH medians, never the stable one alone",
          f"| **{r_med:.0f}** | **{rrpub['median']:.0f}** |" in rr_md
          or (f"**{r_med:.0f}**" in rr_md and f"**{rrpub['median']:.0f}**" in rr_md),
          f"screen-level {r_med:.0f} and publication-level {rrpub['median']:.0f}")

    # Both gates are the arm's licence to exist. If either is ever recorded as
    # failed while the outputs remain, the outputs were written against a broken
    # join and every number above is noise.
    rg = rrj["sanity_gates"]
    check("corpus rerank: the join gate is recorded as passed",
          rg["join"]["screens_matched_row_for_row"] == len(rper)
          and rg["join"]["max_abs_r2_delta_vs_committed"] <= 1e-6)
    check("corpus rerank: the own-screen gate reproduces the published 3 of 10 "
          "above the corpus 90th percentile",
          rg["own_screen"]["above_p90"]
          and near(rg["own_screen"]["r2_size_alone"], 0.4649)
          and near(rg["own_screen"]["corpus_p90"],
                   float(per.r2_size_alone.quantile(0.90)))
          and rg["own_screen"]["survivors_top10"] == 3,
          f"own R2 {rg['own_screen']['r2_size_alone']} vs p90 "
          f"{rg['own_screen']['corpus_p90']}, {rg['own_screen']['survivors_top10']}/10")
    # The result that bounds this project rather than flattering it: our own screen
    # is at the churning tail, not the middle. Stated in the doc, checked here.
    _own_pct = 100 * float((rper.survivors_top10 <= 3).mean())
    check("corpus rerank: the doc states how atypical our own 3-of-10 is",
          f"{_own_pct:.1f}%" in rr_md, f"recomputed {_own_pct:.1f}% at or below 3/10")

    check("corpus rerank: labelled post-hoc, not pre-registered, in both surfaces",
          "not pre-registered" in rr_md.lower()
          and "not pre-registered" in rrj["status"].lower())
    check("corpus rerank: the estimand warning survives in both surfaces",
          "estimand" in rr_md.lower() and "estimand_warning" in rrj)
    check("corpus rerank: the arm states it nominates nothing",
          "nominates" in rr_md.lower() or "not a candidate" in rr_md.lower())
    # Same scope rule as evaluation 10: the unit of inference is the distribution.
    _rr_named = [p for p in pmids
                 if re.search(rf"(?<![\d.]){re.escape(p)}(?![\d.])", rr_md)]
    _rr_tok = re.findall(r"SCREEN[_ ]?\d+", rr_md)
    check("corpus rerank scope: no screen or publication named in the arm's README",
          not _rr_named and not _rr_tok,
          f"found {(_rr_named + _rr_tok)[:5]}" if _rr_named or _rr_tok else "")

    # Same failure mode, different number: controls.csv is the only truth.
    n_ctrl, n_ctrl_fail = len(controls), int((controls.verdict == "FAIL").sum())
    words = {3: "three", 4: "four", 5: "five", 6: "six", 7: "Seven", 8: "eight"}
    claim = (f"**{words[n_ctrl]} controls with published outcomes, "
             f"{words[n_ctrl_fail]} of them failing**")
    # Detail is printed on PASS lines too, so word it as a statement of fact
    # rather than as a failure: "README lacks ..." on a PASS line reads as a bug.
    check("README controls count matches controls.csv", claim in report_readme,
          f"frozen: {n_ctrl} controls / {n_ctrl_fail} FAIL; README must say {claim!r}")

    # ---------------- app.py actually renders ----------------
    # Every other check on app.py reads its SOURCE. That is how the MCP server
    # shipped working from exactly one directory: the source was fine and
    # nobody ran it the way a stranger would. Streamlit's own headless harness
    # executes the script top to bottom in ~1.3 s, so there is no excuse for
    # asserting about a page nobody has rendered.
    try:
        from streamlit.testing.v1 import AppTest       # noqa: E402
        at = AppTest.from_file(str(ROOT / "app.py"), default_timeout=120).run()
        rendered = " ".join(str(m.value) for m in at.markdown)             + " " + " ".join(str(s.value) for s in at.subheader)
        check("app.py renders without raising",
              len(at.exception) == 0,
              f"{len(at.exception)} exception(s): "
              f"{[str(e.value)[:90] for e in at.exception]}"
              if len(at.exception) else
              f"{len(at.markdown)} markdown / {len(at.subheader)} subheader / "
              f"{len(at.dataframe)} dataframe blocks")
        # and it renders the counts, not just contains them in source
        check("app.py renders the evaluation counts it claims",
              f"{_WORDS[n_neg].capitalize()} of {_WORDS[n_eval]} evaluations"
              in rendered,
              f"looking for '{_WORDS[n_neg].capitalize()} of {_WORDS[n_eval]} "
              f"evaluations' in the RENDERED output")
    except ImportError:
        check("app.py renders without raising", False,
              "streamlit.testing.v1 unavailable — this check cannot silently skip")

    # ---------------- independent recomputation ----------------
    # The strongest validation artifact here: a second implementation of the
    # headline statistic, written from the README method section without
    # reading src/score_k562.py, using scipy's Mann-Whitney and statsmodels'
    # BH and OLS in place of the frozen path's own. If the two ever diverge,
    # the headline depends on one implementation rather than on the data, and
    # that has to fail the build rather than sit in a JSON nobody opens.
    indep_p = ROOT / "results" / "independent" / "independent_recompute.json"
    if indep_p.exists():
        ind = json.loads(indep_p.read_text())
        tol = ind["tolerance"]
        got = ind["headline_recomputed_on_independent_R_p"]
        pub = ind["published"]
        for k in pub:
            check(f"independent recomputation agrees on {k}",
                  abs(got[k] - pub[k]) <= tol,
                  f"published {pub[k]} vs independent {got[k]} "
                  f"(tolerance {tol})")
        st = ind["per_program_statistic"]
        check("independent recomputation reproduces R_p on every program",
              st["n_programs"] == len(summary)
              and st["pearson_r_vs_frozen_R_p"] >= 0.999
              and st["max_abs_diff_R_p"] < 1e-3,
              f"n={st['n_programs']} pearson={st['pearson_r_vs_frozen_R_p']} "
              f"max|diff|={st['max_abs_diff_R_p']}")
        # The published figures it is checked against must be the ones the repo
        # actually claims, not a copy that can drift.
        check("independent recomputation is checked against the published figures",
              near(pub["size_alone"], float(sens["set_size_alone"]["r2"]))
              and near(pub["all_six"], float(sens["all_six"]["adj_r2"]), 1e-3),
              f"json {pub} vs stripped_model.json")
        # It must not silently become a re-read of the frozen answer. Naive
        # version of this checked that "n_hits_q05" never appears in the module
        # -- but it legitimately does, as the column the independent result is
        # COMPARED against. Structure, not substrings: the independent hit
        # count has to come out of score_program(), and score_program() has to
        # go through scipy and statsmodels rather than the frozen csv.
        rec = (ROOT / "src" / "independent_recompute.py").read_text()
        import ast, importlib
        import numpy as _np
        _ir = importlib.import_module("src.independent_recompute")
        tree = ast.parse(rec)
        fn = next((n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)
                   and n.name == "score_program"), None)
        calls = {n.func.id for n in ast.walk(fn) if isinstance(n, ast.Call)
                 and isinstance(n.func, ast.Name)} if fn else set()
        check("independent recomputation computes hits rather than reading them",
              fn is not None
              and {"mannwhitneyu", "multipletests"} <= calls
              and '"n_hits_indep": hits' in rec
              and _ir.RAW.parent.name == "raw" and _ir.RAW.exists() is not None,
              f"score_program calls {sorted(calls)}" if fn else "no score_program")
        # And it must actually work: run its scorer on synthetic data whose
        # answer is known by construction. A separated block must produce hits;
        # an identical block must produce none.
        rng = _np.random.default_rng(0)
        Xs = rng.normal(size=(60, 200))
        Xs[:, :20] += 6.0                      # members clearly shifted
        mem, bg = _np.arange(20), _np.arange(20, 200)
        hits_sep, _ = _ir.score_program(Xs, mem, bg)
        Xn = rng.normal(size=(60, 200))        # nothing shifted
        hits_null, _ = _ir.score_program(Xn, mem, bg)
        check("independent scorer separates a planted signal from a null",
              hits_sep >= 55 and hits_null <= 6,
              f"planted={hits_sep}/60 perturbations, null={hits_null}/60")

    # ---------------- evaluation 11: the literature arm ----------------
    # Live-index arm, so the numbers are a dated observation and not
    # reproducible by `make all`. What IS checkable is that the doc, the README
    # row and the stored JSON agree, that the power rule was honoured, and that
    # the positive control passed -- without which a low rate is a dead regex.
    lit_json = ROOT / "results" / "literature" / "literature_audit.json"
    lit_ctrl = ROOT / "results" / "literature" / "positive_control.json"
    lit_doc = ROOT / "docs" / "LITERATURE.md"
    if lit_json.exists():
        lit = json.loads(lit_json.read_text())
        litmd = lit_doc.read_text() if lit_doc.exists() else ""
        lit_row = re.search(r"^\|\s*\d+\s*\|\s*Does the field say so\?.*$",
                            report_readme, re.M)

        n_q = lit["n_publications_queried"]
        n_r = lit["n_resolved_to_full_text"]
        n_a = lit["tier_a_explicit_size"]["n"]
        pct_a = lit["tier_a_explicit_size"]["of_resolved"]

        # The search terms are part of what was sealed, so the code must
        # implement exactly the set the pre-registration fixed -- no more, no
        # fewer. The first run shipped 7 of the 8 Tier A terms because one was
        # dropped in transcription, and nothing here noticed. Parse the terms
        # out of the fenced block in the pre-reg and compare to the module.
        prereg = ROOT / "docs" / "LITERATURE_PREREG.md"
        if prereg.exists():
            import importlib
            _lit = importlib.import_module("src.literature_audit")
            pre_txt = prereg.read_text()

            def _terms(header: str) -> set:
                seg = pre_txt.split(header, 1)[1].split("```")[1]
                # A newline separates terms exactly as "|" does -- the sealed
                # block wraps mid-list. Treating it as whitespace glued
                # "size[- ]dependent" to "larger gene sets" and made this
                # guard fail against correct code.
                return {t.strip() for t in seg.replace("\n", "|").split("|")
                        if t.strip()}

            for header, coded, label in (
                    ("**Tier A", set(_lit.TIER_A), "Tier A"),
                    ("**Tier B", set(_lit.TIER_B), "Tier B")):
                sealed = _terms(header)
                check(f"literature: {label} implements exactly the sealed terms",
                      sealed == coded,
                      f"sealed-only {sorted(sealed - coded)} · "
                      f"code-only {sorted(coded - sealed)}"
                      if sealed != coded else f"{len(sealed)} terms")
            check("literature: the pre-registration still hashes to the cited sha256",
                  hashlib.sha256(pre_txt.encode()).hexdigest().startswith("165d91a2"),
                  hashlib.sha256(pre_txt.encode()).hexdigest()[:16])

        check("literature: the query set is the corpus arm's publications",
              n_q == int(per.source_id.nunique()),
              f"arm says {n_q}, corpus_per_screen.csv has {per.source_id.nunique()}")
        check("literature: the pre-registered power rule was applied, not skipped",
              lit["underpowered"] == (n_r < lit["power_floor"]),
              f"resolved {n_r} vs floor {lit['power_floor']}, "
              f"underpowered={lit['underpowered']}")
        check("literature: the verdict matches the branch the numbers select",
              ("NO VERDICT" in lit["verdict"]) if lit["underpowered"]
              else (("(a)" in lit["verdict"]) == (pct_a >= 0.50)),
              lit["verdict"])
        # The whole arm rests on this: a near-zero rate and a broken regex are
        # indistinguishable without a control that must fire.
        if lit_ctrl.exists():
            ctrl = json.loads(lit_ctrl.read_text())
            check("literature: the Tier A positive control fired on every "
                  "methods paper", ctrl["passed"] and ctrl["n_docs"] >= 3,
                  f"{ctrl['n_matched']}/{ctrl['n_docs']} matched")
        else:
            check("literature: the Tier A positive control fired on every "
                  "methods paper", False, "positive_control.json missing")
        check("literature: doc and README row quote the stored numbers",
              all(s in litmd for s in (str(n_q), str(n_r), f"{pct_a*100:.1f}%"))
              and lit_row is not None
              and all(s in lit_row.group(0) for s in (str(n_q), str(n_r),
                                                      f"{pct_a*100:.1f}%")),
              f"n_q={n_q} n_r={n_r} tier_a={pct_a*100:.1f}%")
        check("literature: the open-access denominator is stated in both surfaces",
              "59.4%" in litmd and "59.4%" in (lit_row.group(0) if lit_row else ""),
              "resolution rate must appear beside the fraction, not only in JSON")
        check("literature: labelled as measuring mention rather than understanding",
              "mention, not understanding" in litmd.lower()
              and "mention, not understanding" in (lit_row.group(0) or "").lower())
        # Same scope rule the corpus arm has: aggregate only, no publication named.
        for label, text in {"docs/LITERATURE.md": litmd,
                            "the README literature row":
                                lit_row.group(0) if lit_row else ""}.items():
            named = [p for p in pmids
                     if re.search(rf"(?<![\d.]){re.escape(p)}(?![\d.])", text)]
            check(f"literature scope: no publication named in {label}",
                  not named, f"found {named[:5]}" if named else "")

    # ---------------- demo deep links ----------------
    # docs/DECK.md navigates the live page by anchor during the talk. A renamed
    # or dropped heading id turns a demo beat into a scroll hunt in front of
    # judges, and nothing else in this suite would notice. Anchors are read out
    # of the deck rather than hardcoded here, so adding a beat that jumps
    # somewhere new is covered the moment it is written down.
    deck = (ROOT / "docs" / "DECK.md")
    if deck.exists():
        wanted = sorted(set(re.findall(r"denali/#([a-z][a-z0-9-]*)", deck.read_text())))
        have = set(re.findall(r'<h2 id="([^"]+)"', page))
        missing = [a for a in wanted if a not in have]
        check("every anchor the deck jumps to exists on the page",
              wanted and not missing,
              f"deck links to {len(wanted)}: {', '.join(wanted)}"
              + (f" — MISSING {missing}" if missing else ""))

    # ---------------- the suite counts itself: KEEP THIS LAST ----------------
    # These are hand-typed and therefore drift: the badge said 84, the Tests
    # section said 84, and the plain-language section said 86, while the suite
    # was at 99. A judge who finds a stale test count stops trusting every other
    # number, so the suite now counts itself and checks what the README claims.
    #
    # This block must stay at the bottom of main(). It used to sit mid-file with
    # a hand-maintained "+4" for the checks that followed it, which meant a check
    # added anywhere below was silently uncounted -- the run printed 356 while
    # the self-count still said 355. The offset is now derived from the loop
    # itself, so the only way to break it is to add a check after this point,
    # which is what the comment above is for.
    # Every surface that states the count, not only the README's three. Adding
    # docs/SUBMISSION.md caught this: it restated 355 while the suite was at
    # 356, and nothing here would have noticed, because the patterns all read
    # report_readme. A count is a count wherever it is written down.
    submission = (ROOT / "docs" / "SUBMISSION.md")
    submission_md = submission.read_text() if submission.exists() else ""
    count_claims = [
        (report_readme, r"badge/tests-(\d+)-", "the CI badge"),
        (report_readme, r"\*\*(\d+) assertions\*\*", "the Tests section"),
        (report_readme, r"\*\*(\d+) automated checks\*\*", "the plain-language section"),
        (submission_md, r"\*\*(\d+) automated checks\*\*", "docs/SUBMISSION.md"),
    ]
    total = len(PASS) + len(FAIL) + len(count_claims)
    for src, pat, label in count_claims:
        m = re.search(pat, src)
        stated = int(m.group(1)) if m else -1
        check(f"test count in {label} matches the suite",
              stated == total, f"says {stated}, suite has {total}")

    # ---------------- report ----------------
    for p in PASS:
        print(f"PASS  {p}")
    for f in FAIL:
        print(f"FAIL  {f}")
    print(f"\n{len(PASS)}/{len(PASS) + len(FAIL)} passed")
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
