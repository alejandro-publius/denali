"""Evaluation 8 — is clinical off-target nomination a construction statistic?

POST-HOC. NOT PRE-REGISTERED. Thresholds are SWEPT, not chosen — the same
labelling as evaluation 6, and for the same reason: this arm was built after the
freeze, so no single threshold in it is entitled to be called the deciding one.
Every hit rule we could defend is reported, and the spread is the result.

The question this project keeps asking is whether a ranking measures biology or
measures how the ranking was built. Two published datasets, neither ours, let us
ask it where the answer has a patient at the end of it.

ARM 1 — CHANGE-seq (Lazzarotto et al., Nat Biotechnol 2020,
doi:10.1038/s41587-020-0555-7), Supplementary Tables 3 and 6.
202,043 biochemically nominated off-target sites over 110 guides; ST6 is
GUIDE-seq, a *cellular* assay, on 56 of the same guides. Two assays, same
guides, different physical principle — a genuine paired arm, and the closest
thing to a replication test the off-target field has.

The confound is the same one, wearing different clothes. In our own data a
gene set's SIZE inflated its hit count. Here a guide's SEARCH YIELD — how many
candidate sites the mismatch budget nominated for it — does the same job. A
guide whose search returns 6,000 sites has more chances to be confirmed than one
returning 200, and that is arithmetic, not guide biology.

ARM 2 — CRISPRme (Cancellieri et al., Nat Genet 2022,
doi:10.1038/s41588-022-01257-y), Supplementary Data 2. Top-1000 sites by CFD for
each of 14 therapeutic guides.

  WHAT IS NOT NEW: that genetic variants create off-target sites is the finding
  of the CRISPRme paper itself. Recovering it is not a discovery and is not
  presented as one.

  WHAT THIS ADDS: the per-guide fraction, framed as a construction statistic —
  and the distinction between two things that are easy to conflate. A site whose
  best alignment comes from an alt allele is not the same as a site that does not
  exist in the reference at all. Both are reported, separately, because the first
  is roughly three and a half times the second and the looser one is the number
  that sounds alarming.

  THE DENOMINATOR IS NOT THE GENOME. It is the top 1,000 by CFD per guide — a
  ranked selection. Every percentage in arm 2 is a share of that selection.

Writes results/offtarget/ ONLY. Never touches results/frozen/.

    .venv/bin/python -m src.offtarget_audit
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from src.audit_screen import audit_replication

DATA = Path("data/offtarget")
OUT = Path("results/offtarget")

# Swept, not chosen. Read-count thresholds spanning the range any of these
# papers would defend, from "any read at all" to a stringent cutoff. The result
# is the SPREAD across all seven; no single row is the headline.
HIT_RULES = [1, 5, 10, 25, 50, 100, 250]

# Arm 2 needs no threshold: both quantities are categorical columns in the sheet.
ALT_ORIGIN = "REF/ALT_origin_(highest_CFD)"
NOT_IN_REF = "Not_found_in_REF"
PAM_CREATE = "PAM_creation_(highest_CFD)"


def _yn(s: pd.Series) -> pd.Series:
    return s.astype(str).str.strip().str.lower()


def arm1_changeseq() -> dict:
    """Two assays, same guides. How much of their agreement is search yield?"""
    p = DATA / "changeseq.xlsx"
    bio = pd.read_excel(p, sheet_name="CHANGE-seq_Supp_Table_3")   # biochemical
    cell = pd.read_excel(p, sheet_name="CHANGE-seq_Supp_Table_6")  # cellular

    shared = sorted(set(bio.name) & set(cell.name))
    b = bio[bio.name.isin(shared)]
    c = cell[cell.name.isin(shared)]

    # search yield: how many candidate sites the biochemical search nominated.
    # This is the analogue of gene-set size, and it is a property of the search,
    # not of the guide's biology.
    yield_ = b.groupby("name").size().reindex(shared).fillna(0)

    # Numerator and denominator must come from the SAME subset. Counting the
    # permissive tail over the 56 paired guides and dividing by all 202,043 sites
    # is the mismatched-subset error this project has already made once on the
    # results page; the mismatch profile below is over the full ST3, stated as such.
    mismatch = bio.distance.value_counts().sort_index()
    permissive = int(mismatch.reindex([5, 6]).fillna(0).sum())

    sweep = []
    for t in HIT_RULES:
        hits_a = (b[b.CHANGEseq_reads >= t].groupby("name").size()
                  .reindex(shared).fillna(0))
        hits_b = (c[c.GUIDEseq_reads >= t].groupby("name").size()
                  .reindex(shared).fillna(0))
        if hits_b.sum() == 0 or hits_a.sum() == 0:
            sweep.append({"read_threshold": t, "verdict": "NO HITS AT THIS RULE"})
            continue
        rep = audit_replication(yield_.values, hits_a.values, hits_b.values)
        # variance in cellular confirmations explained by search yield alone
        r2 = float(np.corrcoef(np.log10(1 + yield_.values),
                               np.log10(1 + hits_b.values))[0, 1] ** 2)
        # the same regression in the biochemical direction, which is circular:
        # a nominated site with >=1 read is a hit by construction, so at the
        # lowest thresholds this is an identity and returns exactly 1.
        r2_taut = float(np.corrcoef(np.log10(1 + yield_.values),
                                    np.log10(1 + hits_a.values))[0, 1] ** 2)
        sweep.append({
            "read_threshold": t,
            "guides": int(len(shared)),
            "raw_agreement_spearman": rep["raw_agreement_spearman"],
            "agreement_after_removing_search_yield": rep["agreement_after_removing_size"],
            "share_of_agreement_that_is_search_yield": rep["share_of_agreement_that_is_size"],
            "r2_search_yield_predicts_cellular_hits": round(r2, 4),
            "r2_search_yield_predicts_BIOCHEMICAL_hits_TAUTOLOGICAL": round(r2_taut, 4),
            "verdict": rep["verdict"],
        })

    scored = [s for s in sweep if "share_of_agreement_that_is_search_yield" in s]
    shares = [s["share_of_agreement_that_is_search_yield"] for s in scored]
    r2s = [s["r2_search_yield_predicts_cellular_hits"] for s in scored]

    return {
        "dataset": "CHANGE-seq, Lazzarotto et al. Nat Biotechnol 2020",
        "doi": "10.1038/s41587-020-0555-7",
        "tables": ["Supplementary Table 3 (CHANGE-seq, biochemical)",
                   "Supplementary Table 6 (GUIDE-seq, cellular)"],
        "sites_nominated_total": int(len(bio)),
        "guides_biochemical": int(bio.name.nunique()),
        "guides_cellular": int(cell.name.nunique()),
        "guides_paired": len(shared),
        "search_yield_per_guide": {
            "min": int(yield_.min()), "median": int(yield_.median()),
            "max": int(yield_.max()),
            "fold_range": round(float(yield_.max() / max(1, yield_.min())), 1)},
        "mismatch_distribution": {int(k): int(v) for k, v in mismatch.items()},
        "share_at_5_or_6_mismatches": round(permissive / len(bio), 4),
        "hit_rules_swept": HIT_RULES,
        "sweep": sweep,
        "share_of_agreement_that_is_search_yield": {
            "min": min(shares), "median": round(float(np.median(shares)), 4),
            "max": max(shares)},
        "r2_search_yield_predicts_cellular_hits": {
            "min": min(r2s), "max": max(r2s)},
        "reading": (
            f"Across {len(scored)} hit rules, between {min(shares):.0%} and "
            f"{max(shares):.0%} of the agreement between a biochemical and a "
            f"cellular off-target assay is explained by how many sites the search "
            f"nominated, not by the guide. Median {np.median(shares):.1%}."),
        "why_it_matters": (
            "Agreement between two assays is the strongest evidence an off-target "
            "list gets before it is used to pick a clinical guide. Both assays "
            "inherit the same candidate search, so a guide can agree with itself "
            "for the same wrong reason twice. This is the cross-screen finding "
            "from our own data (26%) reappearing in a domain where the stakes are "
            "clinical — modestly stronger, not dramatically so."),
        "a_tautology_we_refused_to_report": (
            "Regressing search yield on the BIOCHEMICAL hit count gives R^2 "
            "0.83-1.00, and exactly 1.0000 at the two lowest thresholds. That is "
            "not a finding: every nominated site has at least one read, so at "
            "those rules the hit count IS the yield and the regression is an "
            "identity. The reported R^2 is yield against the CELLULAR hit count "
            "(0.36-0.55), which is the only direction that can carry information. "
            "The tautological figure is recorded here because it is the number "
            "this arm would have overstated itself with."),
        "r2_tautological_biochemical_direction": [
            s["r2_search_yield_predicts_BIOCHEMICAL_hits_TAUTOLOGICAL"]
            for s in scored],
        "limits": (
            "56 paired guides, one lab, two assays. GUIDE-seq detects far fewer "
            "sites than CHANGE-seq by construction, so the cellular hit counts "
            "are small and the agreement estimate is correspondingly noisy. "
            "Read-count thresholds are swept because none of them is privileged."),
    }


def arm2_crisprme() -> dict:
    """How much of a therapeutic guide's top-ranked off-target list is variant-driven?"""
    xl = pd.ExcelFile(DATA / "crisprme.xlsx")
    rows = []
    for s in xl.sheet_names:
        d = pd.read_excel(xl, sheet_name=s)
        rows.append({
            "guide_sheet": s,
            "n_sites_ranked": int(len(d)),
            "alt_allele_best_alignment": int((_yn(d[ALT_ORIGIN]) == "alt").sum()),
            "absent_from_reference": int((_yn(d[NOT_IN_REF]) == "y").sum()),
            "pam_creating_variants": int(d[PAM_CREATE].notna().sum()),
        })
    T = pd.DataFrame(rows)
    n = int(T.n_sites_ranked.sum())
    alt = int(T.alt_allele_best_alignment.sum())
    absent = int(T.absent_from_reference.sum())
    f_alt = T.alt_allele_best_alignment / T.n_sites_ranked
    f_abs = T.absent_from_reference / T.n_sites_ranked

    return {
        "dataset": "CRISPRme, Cancellieri et al. Nat Genet 2022",
        "doi": "10.1038/s41588-022-01257-y",
        "table": "Supplementary Data 2 — top 1,000 sites by CFD per guide",
        "guides": int(len(T)),
        "sites_ranked_total": n,
        "alt_allele_best_alignment": {
            "n": alt, "fraction": round(alt / n, 4),
            "per_guide_min": round(float(f_alt.min()), 4),
            "per_guide_max": round(float(f_alt.max()), 4),
            "means": ("the site's HIGHEST-CFD alignment comes from an alternate "
                      "allele — the variant makes it a BETTER match. The site may "
                      "still exist in the reference genome.")},
        "absent_from_reference": {
            "n": absent, "fraction": round(absent / n, 4),
            "per_guide_min": round(float(f_abs.min()), 4),
            "per_guide_max": round(float(f_abs.max()), 4),
            "means": ("the site does not exist in the reference genome at all. "
                      "This is the strict reading of 'only on a non-reference "
                      "allele', and it is roughly a third of the looser one.")},
        "pam_creating_variants_per_guide": {
            "min": int(T.pam_creating_variants.min()),
            "max": int(T.pam_creating_variants.max())},
        "per_guide": T.to_dict("records"),
        "not_a_discovery": (
            "That variants create off-target sites is the finding of the CRISPRme "
            "paper itself. Recovering it here confirms the pipeline reads the data "
            "correctly; it is not presented as new."),
        "what_is_added": (
            "The per-guide fraction as a construction statistic, and the separation "
            "of two quantities that are easy to conflate: "
            f"{alt / n:.1%} of ranked sites score best on an alt allele, but only "
            f"{absent / n:.1%} are absent from the reference. Quoting the first "
            "while describing the second overstates the effect roughly threefold."),
        "denominator_warning": (
            "The denominator is the top 1,000 by CFD per guide — a RANKED "
            "SELECTION, not the genome. These are shares of a shortlist that was "
            "already sorted by predicted activity."),
    }


def main() -> None:
    a1 = arm1_changeseq()
    a2 = arm2_crisprme()
    res = {
        "evaluation": 8,
        "title": "Off-target nomination as a construction statistic",
        "status": "POST-HOC, NOT PRE-REGISTERED. Thresholds SWEPT, not chosen.",
        "same_labelling_as": "evaluation 6 (engagement), for the same reason",
        "data_provenance": "two published datasets, neither generated by this project",
        "arm1_assay_concordance": a1,
        "arm2_variant_driven_sites": a2,
        "scope": (
            "No guide is named safe or unsafe. These are properties of how "
            "off-target lists are CONSTRUCTED, not verdicts on any guide, and a "
            "tool that turned a confound estimate into a clinical recommendation "
            "would be committing the error it exists to detect."),
        "does_not_revise": "the pre-registered K562 primary in results/frozen/",
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "offtarget_evaluation.json").write_text(json.dumps(res, indent=2) + "\n")
    pd.DataFrame(a1["sweep"]).to_csv(OUT / "changeseq_sweep.csv", index=False)
    pd.DataFrame(a2["per_guide"]).to_csv(OUT / "crisprme_per_guide.csv", index=False)

    sh = a1["share_of_agreement_that_is_search_yield"]
    print("=" * 72)
    print("EVALUATION 8 — off-target nomination (POST-HOC, thresholds SWEPT)")
    print("-" * 72)
    print(f"  ARM 1  CHANGE-seq vs GUIDE-seq, {a1['guides_paired']} paired guides")
    print(f"         {a1['sites_nominated_total']:,} sites nominated over "
          f"{a1['guides_biochemical']} guides")
    print(f"         {a1['share_at_5_or_6_mismatches']:.1%} sit at 5-6 mismatches")
    print(f"         agreement that is SEARCH YIELD: {sh['min']:.0%}-{sh['max']:.0%}"
          f"  median {sh['median']:.1%}")
    print(f"  ARM 2  CRISPRme, {a2['guides']} therapeutic guides, "
          f"{a2['sites_ranked_total']:,} ranked sites")
    print(f"         best alignment on an ALT allele : "
          f"{a2['alt_allele_best_alignment']['n']:,} "
          f"({a2['alt_allele_best_alignment']['fraction']:.1%})")
    print(f"         ABSENT from the reference       : "
          f"{a2['absent_from_reference']['n']:,} "
          f"({a2['absent_from_reference']['fraction']:.1%})")
    print("=" * 72)
    print(f"wrote {OUT}/")


if __name__ == "__main__":
    main()
