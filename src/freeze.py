"""Section 1 — freeze the demo interface.

Writes results/frozen/ with FIXED, DOCUMENTED column names. Everything
downstream (MCP server, Streamlit page, Rachel's labels) reads ONLY from here
and never recomputes.

    .venv/bin/python -m src.freeze
"""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import norm
from statsmodels.stats.multitest import multipletests

OUT = Path("results/frozen")
DISC = Path("results/discovery")
SEAL_COMMIT = "9ad74a7"
PREREG_SHA = "d7d90e41332a7c70cf7a5b2d2678ceb9be85d153e0185be2f110e0e3f448d915"
GATE_SHA = "f543b22efe075d034575e105f7a1e5aa31616b4280e302053e7a3967aacb7c55"

TIER_LABEL = {
    "T1_reversal_not_explained_by_fitness":
        "Signal is not explained by the gene being essential",
    "T2_reversal_confounded_by_essentiality":
        "Gene is essential - signal may just be the cell dying",
    "T3_no_fitness_data":
        "No fitness data available for this gene",
}

COLUMNS = ["gene_symbol", "rank", "average_rank", "reversal_score_wilcoxon",
           "reversal_score_cosine", "reversal_effect_size", "q_value",
           "rpe1_rank", "rpe1_covered", "depmap_gene_effect",
           "depmap_n_cell_lines", "is_essential", "tier", "tier_label",
           "k562_chronos", "tier_note"]

# K562 = ACH-000551, the line we actually scored in. `tier`/`tier_label` are
# derived from the 1,178-line MEAN, so they are stale wherever K562 disagrees.
# We do NOT re-tier; we annotate only the rows we actually checked.
K562_MODEL_ID = "ACH-000551"
TIER_NOTE_GENES = ["MBTPS2", "LDLR"]


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def git(*a: str) -> str:
    return subprocess.run(["git", *a], capture_output=True, text=True).stdout.strip()


def k562_chronos() -> pd.Series:
    """Per-gene DepMap gene effect in K562 specifically, not the 1,178-line mean."""
    dm = pd.read_csv("data/raw/CRISPRGeneEffect.csv", index_col=0)
    dm.columns = [c.split(" (")[0] for c in dm.columns]
    return dm.loc[K562_MODEL_ID]


def build_scores(ranked_csv: Path, raw_csv: Path) -> pd.DataFrame:
    r = pd.read_csv(ranked_csv, index_col=0)
    raw = pd.read_csv(raw_csv)
    p = 2 * norm.sf(np.abs(raw.u_z.values))
    raw["q"] = multipletests(p, method="fdr_bh")[1]
    qmin = raw.groupby("target").q.min()

    d = pd.DataFrame(index=r.index)
    d["gene_symbol"] = r.index
    d["average_rank"] = r.avg_rank
    d["reversal_score_wilcoxon"] = r.u_z
    d["reversal_score_cosine"] = r.cosine
    d["reversal_effect_size"] = r.delta
    d["q_value"] = qmin.reindex(r.index)
    d["rpe1_rank"] = r.rpe1_rank
    d["rpe1_covered"] = r.rpe1_covered
    d["depmap_gene_effect"] = r.depmap_chronos
    d["depmap_n_cell_lines"] = r.depmap_n_lines
    d["is_essential"] = r.essential
    d["tier"] = r.tier
    d["tier_label"] = r.tier.map(TIER_LABEL)

    # K562-specific value for every row (a lookup, NOT a re-tiering).
    kc = k562_chronos()
    d["k562_chronos"] = d.gene_symbol.map(kc)

    # tier_note is populated ONLY for rows we actually checked and found stale.
    d["tier_note"] = ""
    for g in TIER_NOTE_GENES:
        m = d.gene_symbol == g
        if m.any():
            v = float(d.loc[m, "k562_chronos"].iloc[0])
            d.loc[m, "tier_note"] = f"essential in K562 (Chronos {v:.3f})"

    d = d.sort_values("average_rank").reset_index(drop=True)
    d.insert(1, "rank", np.arange(1, len(d) + 1))
    return d[COLUMNS]


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)

    a = build_scores(DISC / "upr_ranked.csv", DISC / "k562_upr_reversal.csv")
    b = build_scores(DISC / "chol_ranked.csv", DISC / "k562_chol_reversal.csv")
    a.to_csv(OUT / "program_a_scores.csv", index=False)
    b.to_csv(OUT / "program_b_scores.csv", index=False)
    print(f"program_a_scores.csv  {len(a)} rows")
    print(f"program_b_scores.csv  {len(b)} rows")

    # ---- divergence ----
    dv = pd.read_csv(DISC / "upr_divergence_table.csv", dtype={"pmid": "string"})
    dv = dv.rename(columns={
        "gene": "gene_symbol", "class": "verdict", "pmid": "epmc_pmid",
        "year": "epmc_year", "cited_by": "epmc_cited_by", "hits": "epmc_paper_count",
        "title": "epmc_title", "u_z": "reversal_score_wilcoxon", "q": "q_value",
        "rank": "average_rank"})
    pc = pd.read_csv(DISC / "upr_program_paperclip.csv")
    dv = dv.merge(pc[["gene", "paperclip_pmcid", "paperclip_year", "paperclip_title"]]
                  .rename(columns={"gene": "gene_symbol"}), on="gene_symbol", how="left")
    # NOTE: per-gene verdicts were removed 2026-08-15. -0.019 concordance does not
    # support judging an individual gene. Detail goes to results/discovery/ and the
    # claim-bearing aggregate is written by src/divergence_repair.py.
    dv.to_csv(DISC / "divergence_gene_detail_raw.csv", index=False)
    counts = dv.verdict.value_counts().to_dict()
    print(f"divergence_table.csv  {len(dv)} rows  {counts}")

    # ---- source concentration (Section 4) ----
    def conc(series, label):
        s = series.dropna().astype(str)
        s = s[s != ""]
        vc = s.value_counts()
        return {
            f"{label}_genes_with_a_source": int(len(s)),
            f"{label}_distinct_sources": int(len(vc)),
            f"{label}_sources_per_gene": round(float(len(vc) / len(s)), 4),
            f"{label}_max_genes_on_one_source": int(vc.iloc[0]),
            f"{label}_max_share_one_source": round(float(vc.iloc[0] / len(s)), 4),
            f"{label}_top_source_id": str(vc.index[0]),
            f"{label}_sources_used_for_exactly_one_gene": int((vc == 1).sum()),
            f"{label}_genes_resting_on_exactly_one_source": int(len(s)),
        }
    concentration = {**conc(pc.paperclip_pmcid, "paperclip"),
                     **conc(dv.epmc_pmid, "epmc")}
    print("concentration:", json.dumps(concentration, indent=2)[:400])

    # ---- controls ----
    ctrl = pd.DataFrame([
        dict(control="nonsense_program", program="both",
             what_it_tests="41 random genes, pre-committed seed 20260815. Does the method invent signal from noise?",
             value="0", units="perturbations at q<0.05",
             comparison="517 (program A) / 773 (program B)",
             verdict="PASS", plain="Random genes produce nothing. The method does not manufacture signal."),
        dict(control="known_regulator_recovery", program="program_b",
             what_it_tests="Do canonical cholesterol regulators land at the extremes with the correct sign?",
             value="SREBF2 rank 2; SCAP 27; MBTPS2 49; MBTPS1 56; MYLIP 57; INSIG1 11230; HMGCR 11229; LDLR 11194; HMGCS1 11095",
             units="rank of 11258", comparison="activators at top, negative regulator and synthesis enzymes at bottom",
             verdict="PASS", plain="Every canonical regulator lands at the right end of the list."),
        dict(control="known_regulator_recovery", program="program_a",
             what_it_tests="Do canonical UPR regulators land at the top?",
             value="ATF4 rank 134; ATF6 1590; XBP1 2802; ERN1 5593; EIF2AK3 6946",
             units="rank of 11258", comparison="only ATF4 is near the top",
             verdict="FAIL", plain="The known UPR sensors are not recovered. This is the null."),
        dict(control="guide_pair_concordance", program="both",
             what_it_tests="Do two independent guides against the SAME gene agree?",
             value="-0.019", units="Spearman rho",
             comparison="-0.001 (n=339), +0.029 (n=190), +0.048 (n=93), -0.076 (n=43) at increasing effect-size cuts",
             verdict="FAIL", plain="They do not agree. Gene-level calls are not reproducible. Pathway-level claims only."),
        dict(control="essentiality_matched_null", program="program_a",
             what_it_tests="Is the top of the list just essential genes?",
             value="4.09", units="x enrichment, empirical p<0.001 over 1000 draws",
             comparison="top-50 essential fraction 0.640 vs 0.157 overall",
             verdict="FAIL", plain="Program A's top hits are dominated by genes the cell cannot live without."),
        dict(control="essentiality_matched_null", program="program_b",
             what_it_tests="Is the top of the list just essential genes?",
             value="3.32", units="x enrichment, empirical p<0.001 over 1000 draws",
             comparison="top-50 essential fraction 0.520 vs 0.157 overall; SREBF2 itself is NOT essential (-0.024)",
             verdict="CAVEAT", plain="Enrichment is present, but the headline hit is not essential and sits in Tier 1."),
        dict(control="rpe1_coverage_collision", program="both",
             what_it_tests="Can the replication arm actually reach the interesting genes?",
             value="94.1 vs 11.3", units="% RPE1 coverage, essential vs non-essential",
             comparison="SREBF2, MYLIP, INSIG1, LDLR are all NOT COVERED",
             verdict="FAIL", plain="The replication arm mostly covers genes the toxicity filter flags."),
    ])
    ctrl.to_csv(OUT / "controls.csv", index=False)
    print(f"controls.csv  {len(ctrl)} rows")

    # ---- provenance ----
    data_files = ["data/raw/K562_gwps_normalized_bulk_01.h5ad",
                  "data/raw/rpe1_normalized_bulk_01.h5ad",
                  "data/raw/CRISPRGeneEffect.csv", "data/raw/Model.csv"]
    prov = {
        "generated_by": "src/freeze.py",
        "seal": {
            "commit": SEAL_COMMIT,
            "commit_time": git("show", "-s", "--format=%cI", SEAL_COMMIT),
            "what": "HALLMARK_CHOLESTEROL_HOMEOSTASIS sealed as program B before any scoring",
            "file": "docs/HELDOUT_PROGRAM.md",
        },
        "preregistration_sha256": PREREG_SHA,
        "gate_script_sha256": GATE_SHA,
        "commit_timeline": [
            {"commit": c, "time": git("show", "-s", "--format=%cI", c),
             "subject": git("show", "-s", "--format=%s", c)}
            for c in ["280c626", "9ad74a7", "dcea614", "73d4c33", "7681bc5"]
        ],
        "pipeline_untouched_between_runs": True,
        "pipeline_evidence": {
            "score_k562.py_sha256": sha256(Path("src/score_k562.py")),
            "build2.py_sha256": sha256(Path("src/build2.py")),
            "note": ("Both scripts are byte-identical between the program A and "
                     "program B runs and to the committed copies. The seal commit "
                     "(08:24:14) predates the creation of score_k562.py (08:45:15), "
                     "so the held-out program was fixed before the scoring code existed."),
        },
        "data_checksums_sha256": {f: sha256(Path(f)) for f in data_files if Path(f).exists()},
        "gene_sets": {
            "program_a": "HALLMARK_UNFOLDED_PROTEIN_RESPONSE (MSigDB v2026.1.Hs, 113 genes)",
            "program_b": "HALLMARK_CHOLESTEROL_HOMEOSTASIS (MSigDB v2026.1.Hs, sealed)",
            "hallmark_gmt_sha256": sha256(Path("data/genesets/h.all.v2026.1.Hs.symbols.gmt")),
        },
        "evidence_source_concentration": concentration,
        "scope_limit": ("Guide-pair concordance is -0.019. Gene-level calls are not "
                        "reproducible. Pathway-level claims only. No novel gene is named."),
    }
    (OUT / "provenance.json").write_text(json.dumps(prov, indent=2))
    print("provenance.json written")
    for f in sorted(OUT.iterdir()):
        print(f"  {f.name:26s} {f.stat().st_size/1024:8.1f} KB")


if __name__ == "__main__":
    main()
