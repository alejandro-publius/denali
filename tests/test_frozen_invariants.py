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
    check("no interactive controls on the page",
          not re.search(r"<(button|input|select|form)\b", page, re.I))
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

    # page text = the literal strings app.py renders
    page_text = re.sub(r"<[^>]+>", " ", re.sub(r"<style.*?</style>|<img[^>]*>", " ", page, flags=re.S))
    scan("the page (index.html)", page_text)
    scan("results/figures/CAPTIONS.md", caps)

    # framing rule: the project does not lead with commit ordering
    SEAL = re.compile(r"\bseal(ed|ing)?\b|before the scoring code existed|"
                      r"\d+ minutes? before", re.I)
    for label, txt in [("index.html", page), ("CAPTIONS.md", caps),
                       ("REPORT.md", report)]:
        hit = SEAL.search(txt)
        check(f"no seal framing in {label}", hit is None,
              txt[max(0, hit.start()-60):hit.end()+60].replace("\n", " ") if hit else "")

    check("scope limit is stated on the page", "-0.019" in page or "\u22120.019" in page)
    check("scope limit is stated in the captions",
          "gene-level" in caps or "0.019" in caps or "pointer layer" in caps)

    # ---------------- report ----------------
    for p in PASS:
        print(f"PASS  {p}")
    for f in FAIL:
        print(f"FAIL  {f}")
    print(f"\n{len(PASS)}/{len(PASS) + len(FAIL)} passed")
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
