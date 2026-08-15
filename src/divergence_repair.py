"""ONE-SHOT HISTORICAL MIGRATION. Already run. Not part of `make all`.

⚠ This script CONSUMES AND DELETES its own input. It ran once, on 2026-08-15,
against a results/frozen/divergence_table.csv that no longer exists in this
repository. It cannot run again and it is deliberately excluded from the
reproduction path — a clean-clone check failed on exactly this, which is how the
exclusion was found. It is kept for the record of what was changed and why.

Original purpose — reframe divergence from per-gene verdicts to program-level coverage.

Guide-pair concordance is -0.019, so a per-gene verdict ("knocking out X does NOT
move the program") is a claim our own data does not support. Counting how many
members fall in each class is an AGGREGATE and is supported.

Writes:
  results/frozen/divergence_by_program.csv   claim-bearing, program-level
  results/discovery/divergence_gene_detail.csv  supporting data, NOT claim-bearing,
                                                verdict language removed

    .venv/bin/python -m src.divergence_repair
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

FROZEN = Path("results/frozen")
DISC = Path("results/discovery")
PROGRAM = "HALLMARK_UNFOLDED_PROTEIN_RESPONSE"


def main() -> None:
    d = pd.read_csv(FROZEN / "divergence_table.csv", dtype={"epmc_pmid": "string"})

    # ---- program-level aggregate: the only claim-bearing artifact ----
    n_declared = len(d)
    n_never = int((d.verdict == "UNTESTED").sum())
    n_perturbed = n_declared - n_never
    n_moves = int((d.verdict == "AGREES").sum())
    n_no_move = int((d.verdict == "DISAGREES").sum())
    n_cited = int(d.epmc_pmid.notna().sum())

    agg = pd.DataFrame([{
        "program": PROGRAM,
        "n_members_declared": n_declared,
        "n_members_with_literature": n_cited,
        "n_members_never_perturbed": n_never,
        "n_members_perturbed": n_perturbed,
        "n_members_screen_concordant": n_moves,
        "n_members_screen_discordant": n_no_move,
        "frac_never_perturbed": round(n_never / n_declared, 4),
        "frac_concordant_of_perturbed": round(n_moves / n_perturbed, 4) if n_perturbed else None,
        "distinct_literature_sources": int(d.paperclip_pmcid.nunique()),
        "max_share_one_source": round(
            float(d.paperclip_pmcid.value_counts().iloc[0] / n_cited), 4),
        "coverage_note": (
            f"{n_never} of {n_declared} members were never perturbed in the screen. "
            f"Of the {n_perturbed} that were, {n_moves} moved the program at q<0.05. "
            "These are COUNTS over program members, not verdicts on individual genes."),
    }])
    agg.to_csv(FROZEN / "divergence_by_program.csv", index=False)

    # ---- per-gene detail: demoted out of frozen/, verdict language stripped ----
    g = d.rename(columns={"verdict": "member_class"}).drop(
        columns=[c for c in ["verdict_plain"] if c in d.columns])
    g["member_class"] = g.member_class.map({
        "AGREES": "perturbed_moves_program",
        "DISAGREES": "perturbed_no_detected_move",
        "UNTESTED": "never_perturbed"})
    g["NOT_A_VERDICT"] = (
        "Aggregate input only. Guide-pair concordance is -0.019, so this row is "
        "NOT evidence about this gene. See docs/SCOPE_STATEMENT.md.")
    g.to_csv(DISC / "divergence_gene_detail.csv", index=False)

    (FROZEN / "divergence_table.csv").unlink()

    print("WROTE results/frozen/divergence_by_program.csv")
    print(agg.T.to_string())
    print(f"\nDEMOTED per-gene detail -> {DISC/'divergence_gene_detail.csv'} "
          f"({len(g)} rows, verdict language removed)")
    print("REMOVED results/frozen/divergence_table.csv (carried 113 per-gene verdicts)")


if __name__ == "__main__":
    main()
