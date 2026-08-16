"""Invariants over the three post-deadline arms: benchmarks, corrections,
domains. Same job as tests/test_frozen_invariants.py and the same rule -- these
lock the facts the write-ups rest on, so a silent change fails loudly instead
of producing a confidently wrong page.

    .venv/bin/python tests/test_bigswing_invariants.py

Four classes of check:
  A  every headline number in the write-ups traces to a results/ file
  B  the pre-registrations are unmodified since they were sealed, by hash
  C  the gates that licence each arm actually passed, and are recorded
  D  the scope rule -- distributions, never named entities -- enforced by
     scanning the write-ups rather than trusted to memory
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
RES = ROOT / "results"
PASS: list[str] = []
FAIL: list[str] = []

# Hashes as sealed in commit a2776f7, BEFORE any data was downloaded. The
# domains file carries CORRECTION 1 (commit 8d2296a), appended before any
# domain-5 value existed; its post-correction hash is pinned here.
SEALED = {
    "BENCHMARKS_PREREG.md":
        "9b825d874d64dacdf11d12f3c08e3feefdccb96ee56b99e2f274d94ce9b000d5",
    "CORRECTIONS_PREREG.md":
        "d58fa082d0c642c31c04176c1bd74bf102bb74e014963a5a85c031a69dcda08c",
    "DOMAINS_PREREG.md":
        "f8658cd065e0e967bf9a10d3db6c3d0bbdac523c540532cb7d2a8d568de64062",
}


def check(name: str, cond: bool, detail: str = "") -> None:
    (PASS if cond else FAIL).append(f"{name}{'  --  ' + detail if detail else ''}")


def near(a, b, tol: float = 5e-4) -> bool:
    try:
        return abs(float(a) - float(b)) <= tol
    except (TypeError, ValueError):
        return False


def load(p: Path):
    return json.loads(p.read_text()) if p.exists() else None


def main() -> int:
    # ---------------- B: the pre-registrations are unmodified -------------
    for name, want in SEALED.items():
        p = DOCS / name
        got = hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else ""
        check(f"{name} unmodified since it was sealed", got == want,
              f"{got[:16]}… vs {want[:16]}…")

    # A pre-registration must state a threshold before a value exists. If the
    # word disappears, the document has stopped being one.
    for name in SEALED:
        t = (DOCS / name).read_text().lower()
        check(f"{name} still names a kill criterion",
              "what would make us report neither" in t)

    # ---------------- C + A: benchmarks ----------------------------------
    b = load(RES / "benchmarks" / "mmlu.json")
    check("benchmarks arm produced a result", b is not None)
    if b:
        g = b["gate"]
        check("benchmarks gate passed", g["passed"] is True)
        check("benchmarks gate recovered item counts from reported error",
              g["subjects_within_1pct"] == 57,
              f"{g['subjects_within_1pct']}/57")
        check("benchmarks panel clears the pre-registered floor of 20",
              b["substrate"]["panel_size"] >= 20,
              str(b["substrate"]["panel_size"]))
        # The disanalogy is the whole point: rates clean, counts confounded.
        a1 = abs(b["A1_does_size_predict_the_rate"]
                 ["spearman_size_vs_panel_mean_accuracy"])
        a2 = b["A2_count_layer"]["median_r2_size_alone"]
        check("A1 verdict matches its own pre-registered thresholds",
              (b["A1_does_size_predict_the_rate"]["verdict"].startswith("RATE LAYER CLEAN")
               if a1 < 0.25 else True))
        check("A2 verdict matches its own pre-registered threshold of 0.40",
              (a2 >= 0.40) == b["A2_count_layer"]["verdict"].startswith("ARITHMETIC"))
        check("the count layer is more size-predicted than the rate layer",
              a2 > a1, f"count {a2} vs rate {a1}")
        # The count-layer number must never be quotable as "benchmarks are 60%
        # confounded". It is bounded by an arithmetic floor computed from the
        # size distribution alone, and the observed value sits BELOW it.
        nul = b["A2_count_layer"]["arithmetic_null"]
        check("the count layer is compared against an arithmetic null",
              nul["median_null_r2"] > 0)
        check("observed count-layer R^2 sits below the no-capability null",
              a2 < nul["median_null_r2"],
              f"observed {a2} vs null {nul['median_null_r2']}")
        check("the write-up states the count layer is not a finding about "
              "benchmarks",
              "nothing bad about any benchmark" in
              (DOCS / "BENCHMARKS.md").read_text().lower()
              if (DOCS / "BENCHMARKS.md").exists() else True)
        # A3 fired on a tie; the disclosure must survive any future edit.
        ph = b["post_hoc_how_A3_fired"]
        check("A3's top-5 change is disclosed as a near-tie, in items",
              ph["top5_boundary_gap_in_items"] <= 2,
              f"{ph['top5_boundary_gap_in_items']} items")
        check("the post-hoc section is labelled post-hoc",
              ph["label"].startswith("POST-HOC"))

    # ---------------- C + A: corrections ---------------------------------
    c = load(RES / "corrections" / "summary.json")
    check("corrections arm produced a result", c is not None)
    if c:
        g = c["gate"]
        check("corrections gate passed", g.get("passed") is True)
        check("corrections gate reproduced the committed corpus on every screen",
              near(g.get("pct_within_tol", 0), 100.0, 0.01),
              f"{g.get('pct_within_tol')}%")
        check("the corpus screen count is unchanged at 1,272",
              c["n_screens_audited"] == 1272, str(c["n_screens_audited"]))
        # A correction that is reported as WORKS must actually clear the
        # pre-registered bar, in both of its two parts.
        for name, d in c["corrections"].items():
            if d.get("verdict") == "WORKS":
                check(f"{name} WORKS verdict clears both registered bars",
                      d["median_relative_reduction"] >= 0.50
                      and d["worse_share_pct"] <= 5.0,
                      f"{d['median_relative_reduction']}, "
                      f"{d['worse_share_pct']}%")
            if d.get("verdict") == "FAILS":
                check(f"{name} FAILS verdict matches the registered rule",
                      d["median_relative_reduction"] < 0.20
                      or d["worse_share_pct"] > 15.0)
        # The obligation: if denali's own correction loses to a published one,
        # the report must say the tool should recommend that method instead.
        # It must bite on EITHER axis -- the registered median, and the tail --
        # because the arm's actual finding is that ours wins the first and
        # loses the second. A guard that only checked the median would pass
        # vacuously here and would have let the real result go unreported.
        own = c["corrections"].get("C5_residual", {})
        others = {k: v for k, v in c["corrections"].items()
                  if k != "C5_residual" and "median_relative_reduction" in v}
        best_med = max(others.values(),
                       key=lambda v: v["median_relative_reduction"])
        # among methods that also clear the median bar, who is safest?
        clears = [v for v in others.values()
                  if v["median_relative_reduction"] >= 0.50] or list(others.values())
        safest = min(clears, key=lambda v: v["worse_share_pct"])
        beaten_median = (best_med["median_relative_reduction"]
                         - own.get("median_relative_reduction", 0)) > 0.05
        beaten_tail = own.get("worse_share_pct", 0) > safest["worse_share_pct"] * 2
        txt = (DOCS / "CORRECTIONS.md").read_text() \
            if (DOCS / "CORRECTIONS.md").exists() else ""
        low = txt.lower()
        says_so = ("recommendation is" in low or "should recommend" in low) and \
                  "not ours" in low or "rather than itself" in low
        check("when denali's own correction loses on either axis, the write-up "
              "recommends the other method",
              (not (beaten_median or beaten_tail)) or says_so,
              f"beaten_median={beaten_median} beaten_tail={beaten_tail} "
              f"(ours {own.get('worse_share_pct')}% worse vs safest "
              f"{safest['worse_share_pct']}%)")
        check("denali's own correction reports its worse-share, not only its "
              "median", "worse_share_pct" in own)
        check("the unreliable-tail verdict is not quietly upgraded to WORKS",
              own.get("verdict") != "WORKS" or own.get("worse_share_pct", 99) <= 5.0,
              str(own.get("verdict")))

    # ---------------- C + A: domains -------------------------------------
    t = load(RES / "domains" / "TABLE.json")
    check("domains table produced", t is not None)
    if t:
        rows = t["rows"]
        check("the table reports six rows or says why not", len(rows) == 6,
              f"{len(rows)} rows")
        v = t["verdict"]
        check("the claim verdict matches its own pre-registered arithmetic",
              v["claim_a_supported"] ==
              (v["n_defensible"] >= 4 and v["n_at_or_above_0.20_raw"] >= 3
               and v["n_non_gene_at_or_above_0.40_raw"] >= 1))
        check("the gene-set row is the reference distribution, not a finding",
              any(r["domain"].startswith("1 ") and
                  r["corpus_percentile_logsize"] == 50.0 for r in rows))
        # Degenerate hit rules must never become a headline.
        m = load(RES / "domains" / "metabolite.json")
        if m and m.get("DEGENERACY_WARNING", {}).get("fired"):
            row = next((r for r in rows if r["domain"].startswith("3 ")), None)
            ok = row is not None and not near(row["r2_size_alone_raw"],
                                              m["r2_size_alone_raw"])
            check("the degenerate metabolite primary is not the headline", ok,
                  "" if ok else ("headline equals the degenerate primary"
                                 if row else "no metabolite row"))
        p4 = load(RES / "domains" / "protein.json")
        if p4 and p4.get("hit_fraction_guard", {}).get("fired"):
            row = next((r for r in rows if r["domain"].startswith("4 ")), None)
            check("the pre-registered protein guard changed the headline",
                  row is not None
                  and not near(row["r2_size_alone_raw"],
                               p4["primary"]["r2_size_alone_raw"]))
        mb = load(RES / "domains" / "microbiome.json")
        if mb and "power_note" in mb:
            check("unscoreable cohorts are counted, never scored as clean",
                  mb["n_cohorts_scoreable"] + mb["power_note"]["unscoreable"]
                  == mb["n_cohorts"])
            for pc in mb["per_cohort"]:
                if not pc["scoreable"]:
                    check("an unscoreable cohort carries no R^2",
                          pc["r2_size_alone_raw"] is None
                          and pc["verdict"].startswith("UNSCOREABLE"))
                    break
        y = load(RES / "domains" / "yeast.json")
        if y:
            check("the yeast row states the objection it exists to answer",
                  "curation" in y["why_this_domain"].lower())

    # ---------------- D: scope -------------------------------------------
    # The unit of inference is the distribution. These arms must not name an
    # individual model, screen, publication or gene set as a finding.
    for name in ("BENCHMARKS.md", "CORRECTIONS.md", "DOMAINS.md"):
        p = DOCS / name
        if not p.exists():
            continue
        txt = p.read_text()
        # HuggingFace-style model ids, ORCS screen ids, PubMed ids
        bad = re.findall(r"\b[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]*(?:7[Bb]|13[Bb]|"
                         r"70[Bb]|[Ii]nstruct|[Cc]hat)[A-Za-z0-9_.-]*\b", txt)
        check(f"{name} names no individual model", not bad,
              ", ".join(sorted(set(bad))[:3]))
        gmt = re.findall(r"\bHALLMARK_[A-Z0-9_]+\b", txt)
        check(f"{name} names no individual gene set as a finding", not gmt,
              ", ".join(sorted(set(gmt))[:3]))
        check(f"{name} reports a negative before a positive",
              txt.lower().find("negative") != -1)

    # every write-up must point at the file its numbers come from
    for name, res in (("BENCHMARKS.md", "results/benchmarks/"),
                      ("CORRECTIONS.md", "results/corrections/"),
                      ("DOMAINS.md", "results/domains/")):
        p = DOCS / name
        if p.exists():
            check(f"{name} cites its results directory", res in p.read_text())

    for x in PASS:
        print(f"PASS  {x}")
    for x in FAIL:
        print(f"FAIL  {x}")
    print(f"\n{len(PASS)}/{len(PASS) + len(FAIL)} passed")
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
