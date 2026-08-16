"""Track C — the six-row table. One recipe, six domains that share no biology.

Pre-registered in docs/DOMAINS_PREREG.md (6d40a079..., a2776f7) with
CORRECTION 1 (8d2296a). This module assembles ONLY; every number it prints was
computed by the per-domain module and is read back from results/domains/.

The deciding claim, fixed before any domain ran:
  (a) "it is arithmetic" -- at least 4 of 6 rows yield a defensible number AND
      at least 3 of those reach the tool's PARTIAL line (raw-size R^2 >= 0.20)
      AND at least one NON-GENE domain reaches CONFOUNDED (>= 0.40)
  (b) otherwise -- the confound does not travel at the strength claimed, and
      that is the reported headline

"No defensible number here" is a valid entry and is printed as such. Where a
domain's registered hit rule turned out to be degenerate, the row carries the
usable variant and the degenerate primary is printed beside it, never instead
of it.

Writes results/domains/TABLE.json and results/domains/TABLE.md.

    .venv/bin/python -m src.domains_table
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

D = Path("results/domains")
CORPUS = Path("results/corpus/corpus_per_screen.csv")
CORPUS_JSON = Path("results/corpus/corpus_audit.json")


def load(name: str):
    p = D / f"{name}.json"
    return json.loads(p.read_text()) if p.exists() else None


def row(domain, substrate, n_sets, size_range, raw, log, verdict, pct,
        surv, note, headline_source):
    return {
        "domain": domain, "substrate": substrate, "n_sets": n_sets,
        "size_range": size_range, "r2_size_alone_raw": raw,
        "r2_size_alone_log": log, "verdict": verdict,
        "corpus_percentile_logsize": pct,
        "rerank_top10_survived": surv, "note": note,
        "headline_source": headline_source,
    }


def main() -> int:
    rows = []

    # 1 — gene sets. Pre-event work, cited not recomputed.
    ca = json.loads(CORPUS_JSON.read_text())
    corpus = pd.read_csv(CORPUS)
    rows.append(row(
        "1 · gene sets (CRISPR screens)",
        "BioGRID ORCS 2.0.18 x Hallmark, 1,272 screens",
        f"50 per screen", "varies by screen",
        ca["median_r2_raw_size_predictor"], ca["quantiles"]["p50"],
        "reference distribution", 50.0, None,
        "Pre-event work, cited not recomputed. This IS the reference "
        "distribution the other rows are placed against, so its percentile is "
        "50 by construction.",
        "results/corpus/corpus_audit.json"))

    # 6 — yeast. Run first: it kills the sloppy-curation objection.
    y = load("yeast")
    if y:
        p = y["primary"]
        rows.append(row(
            "6 · yeast genetic interaction",
            "Costanzo 2016 global network x SGD GO Slim",
            p["n_sets"], p["size_range"], p["r2_size_alone_raw"],
            p["r2_size_alone_log"], p["verdict"],
            y["corpus_percentile_logsize"], p["rerank_top10_survived"],
            "The best-annotated organism in biology. Registered expectation "
            "was 'at or above the corpus 25th percentile'.",
            "results/domains/yeast.json"))

    # 2 — regions
    r = load("regions")
    if r and r.get("status", "").startswith("no defensible"):
        rows.append(row("2 · region sets", "ChIP-Atlas x GWAS Catalog", None,
                        None, None, None, "no defensible number here", None,
                        None, r.get("reason", ""), "results/domains/regions.json"))
    elif r:
        rows.append(row(
            "2 · region sets",
            "ChIP-Atlas hg38 peak calls x GWAS Catalog SNPs",
            r["n_sets"], r["size_range"], r["r2_size_alone_raw"],
            r["r2_size_alone_log"], r["verdict"],
            r["corpus_percentile_logsize"], r["rerank_top10_survived"],
            f"No gene identifiers anywhere. Size is peaks called; "
            f"{r['size_fold_range']}x size range.",
            "results/domains/regions.json"))

    # 3 — metabolites, the boundary condition
    m = load("metabolite")
    if m and m.get("status", "").startswith("no defensible"):
        rows.append(row("3 · metabolite sets", "MetaboAnalyst x SMPDB", None,
                        None, None, None, "no defensible number here", None,
                        None, m.get("reason", ""),
                        "results/domains/metabolite.json"))
    elif m:
        s = m.get("post_hoc_strict_hit_rule", {})
        deg = m.get("DEGENERACY_WARNING", {}).get("fired")
        use = s if (deg and "r2_size_alone_raw" in s) else m
        rows.append(row(
            "3 · metabolite sets (boundary condition)",
            "MetaboAnalyst cachexia x SMPDB",
            m["n_sets"], m["size_range"], use["r2_size_alone_raw"],
            use["r2_size_alone_log"], use["verdict"],
            use["corpus_percentile_logsize"], use.get("rerank_top10_survived"),
            f"Sets are {m['size_range'][0]}-{m['size_range'][1]} members. "
            f"HEADLINE IS THE POST-HOC STRICT-HIT VARIANT: the registered "
            f"BH q<0.05 rule made {m['DEGENERACY_WARNING']['hit_fraction']:.0%} "
            f"of metabolites hits, so hits = rate x size by identity "
            f"(R^2 {m['r2_size_alone_raw']}, printed here and not used).",
            "results/domains/metabolite.json"))

    # 4 — proteins
    p4 = load("protein")
    if p4 and p4.get("status", "").startswith("no defensible"):
        rows.append(row("4 · protein sets", "CPTAC x Reactome", None, None,
                        None, None, "no defensible number here", None, None,
                        p4.get("reason", ""), "results/domains/protein.json"))
    elif p4:
        v = p4.get("registered_variant_top10pct_by_t", {})
        fired = p4["hit_fraction_guard"]["fired"]
        use = v if (fired and "r2_size_alone_raw" in v) else p4["primary"]
        rows.append(row(
            "4 · protein sets",
            "CPTAC COAD proteome x Reactome",
            p4["primary"]["n_sets"], p4["primary"]["size_range"],
            use["r2_size_alone_raw"], use["r2_size_alone_log"], use["verdict"],
            use["corpus_percentile_logsize"], use.get("rerank_top10_survived"),
            f"HEADLINE IS THE REGISTERED VARIANT: the pre-registered "
            f"hit-fraction guard fired at "
            f"{p4['construction']['hit_fraction']:.0%} and required it "
            f"(degenerate primary R^2 {p4['primary']['r2_size_alone_raw']}, "
            f"printed here and not used).",
            "results/domains/protein.json"))

    # 5 — microbiome
    mb = load("microbiome")
    if mb and mb.get("status", "").startswith("no defensible"):
        rows.append(row("5 · microbiome functions", "curatedMetagenomicData",
                        None, None, None, None, "no defensible number here",
                        None, None, mb.get("reason", ""),
                        "results/domains/microbiome.json"))
    elif mb:
        ac = mb["across_cohorts"]
        vd = max(ac["verdicts"], key=ac["verdicts"].get)
        rows.append(row(
            "5 · microbiome functions",
            f"curatedMetagenomicData, {mb['n_cohorts_scoreable']} of "
            f"{mb['n_cohorts']} CRC cohorts scoreable",
            f"{ac['n']} cohorts", ac["size_range_widest"],
            ac["r2_size_alone_raw_median"], ac["r2_size_alone_log_median"],
            f"{vd} ({ac['verdicts'][vd]}/{ac['n']} cohorts)",
            ac["corpus_percentile_logsize_median"],
            ac["rerank_top10_survived_median"],
            f"DEVIATION (correction 1): sets = pathways, members = the species "
            f"carrying them. {mb['power_note']['unscoreable']} of "
            f"{mb['n_cohorts']} cohorts return NO significant stratum and are "
            f"UNSCOREABLE, not scored as clean.",
            "results/domains/microbiome.json"))

    # ---- the pre-registered claim ---------------------------------------
    defensible = [r for r in rows if r["r2_size_alone_raw"] is not None]
    non_gene = [r for r in defensible if not r["domain"].startswith("1 ")]
    at_partial = [r for r in defensible if r["r2_size_alone_raw"] >= 0.20]
    confounded_non_gene = [r for r in non_gene if r["r2_size_alone_raw"] >= 0.40]
    claim_a = (len(defensible) >= 4 and len(at_partial) >= 3
               and len(confounded_non_gene) >= 1)

    verdict = {
        "n_rows": len(rows),
        "n_defensible": len(defensible),
        "n_at_or_above_0.20_raw": len(at_partial),
        "n_non_gene_at_or_above_0.40_raw": len(confounded_non_gene),
        "claim_a_supported": bool(claim_a),
        "claim": ("(a) IT IS ARITHMETIC — the confound appears in domains that "
                  "share no biology" if claim_a else
                  "(b) the confound does not travel at the strength claimed"),
        "thresholds_fixed_in": "docs/DOMAINS_PREREG.md, commit a2776f7, before "
                               "any domain substrate was downloaded",
    }
    out = {
        "status": "Pre-registered in docs/DOMAINS_PREREG.md (6d40a079..., "
                  "a2776f7); CORRECTION 1 at 8d2296a.",
        "recipe": "core.audit raw-size R^2 (verdict line), the log-size variant "
                  "for percentile placement against the committed 1,272-screen "
                  "CRISPR corpus, and core.rerank top-10 survival.",
        "verdict": verdict,
        "rows": rows,
        "caveat": "Percentiles place each domain against the CRISPR corpus "
                  "using the SAME log-size transform on both sides. The raw "
                  "and log columns are different transforms of the same data "
                  "and are never compared to each other.",
        "scope": "No individual set, experiment, cohort, trait or publication "
                 "is named as a finding.",
    }
    (D / "TABLE.json").write_text(json.dumps(out, indent=2) + "\n")

    def f(v, nd=4):
        return "—" if v is None else (f"{v:.{nd}f}" if isinstance(v, float) else str(v))

    md = ["# Track C — one recipe, six domains", "",
          "Pre-registered in `docs/DOMAINS_PREREG.md` (`6d40a079…`, commit "
          "`a2776f7`), correction 1 at `8d2296a`. Every number below was "
          "computed by the per-domain module named in the last column and is "
          "assembled here, not recomputed.", "",
          "| domain | sets | size range | R² size alone (raw) | R² (log) | "
          "verdict | percentile vs 1,272 CRISPR screens | top-10 survive |",
          "|---|---:|---|---:|---:|---|---:|---:|"]
    for r in rows:
        sr = ("—" if r["size_range"] is None else
              (f"{r['size_range'][0]}–{r['size_range'][1]}"
               if isinstance(r["size_range"], list) else str(r["size_range"])))
        md.append(f"| {r['domain']} | {f(r['n_sets'],0)} | {sr} | "
                  f"{f(r['r2_size_alone_raw'])} | {f(r['r2_size_alone_log'])} | "
                  f"{r['verdict']} | {f(r['corpus_percentile_logsize'],1)} | "
                  f"{f(r['rerank_top10_survived'],0)} |")
    md += ["", "## Notes, one per row", ""]
    for r in rows:
        md.append(f"- **{r['domain']}** — {r['note']} `{r['headline_source']}`")
    md += ["", "## The pre-registered claim", "",
           f"**{verdict['claim']}**", "",
           f"- rows with a defensible number: {verdict['n_defensible']}/6 "
           f"(threshold ≥ 4)",
           f"- of those, reaching the tool's PARTIAL line (raw R² ≥ 0.20): "
           f"{verdict['n_at_or_above_0.20_raw']} (threshold ≥ 3)",
           f"- non-gene domains reaching CONFOUNDED (raw R² ≥ 0.40): "
           f"{verdict['n_non_gene_at_or_above_0.40_raw']} (threshold ≥ 1)", "",
           "Thresholds were fixed before any domain substrate was downloaded "
           "and are not revised here.", "",
           "**What this table does not say.** Driving a size correlation to "
           "zero would not prove a ranking correct, and a high R² here does "
           "not mean any particular set is wrong. The unit of inference is the "
           "distribution, and no individual set, experiment, cohort or trait "
           "is named as a finding.", ""]
    (D / "TABLE.md").write_text("\n".join(md) + "\n")
    print("\n".join(md))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
