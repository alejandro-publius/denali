"""Generate denali_audit/atlas.py from results/corpus/corpus_per_screen.csv.

WHY GENERATE IT rather than read the CSV at runtime. The point of the atlas is
that a stranger can cite one screen's no-biology floor and have it mean the same
thing on their machine as on ours. A package that reads a CSV out of a research
repository it was not installed with cannot do that -- `pip install denali-audit`
would produce a tool whose atlas is empty, and the citation would be to a file
the citer does not have.

So the floors are embedded, and the embedding is generated rather than typed.
`tests/test_cross_surface.py` regenerates this file and fails if the committed
one differs, exactly as it does for audit.html, so the atlas and the corpus
cannot drift apart silently.

WHAT IS AND IS NOT EMBEDDED. Only the DERIVED STATISTICS -- the per-screen R^2
values, the counts they were computed from, and the BioGRID screen and PubMed
identifiers needed to attribute them. The descriptive metadata in the corpus CSV
(cell line, phenotype, library) is ORCS's own curation rather than something we
computed, so it stays in the research repo where it already lives and is not
redistributed inside the package.

    .venv/bin/python -m src.build_atlas [--check]
"""
from __future__ import annotations

import hashlib
import pathlib
import sys

import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC = ROOT / "results" / "corpus" / "corpus_per_screen.csv"
OUT = ROOT / "packages" / "denali-audit" / "denali_audit" / "atlas.py"

# Bumped BY HAND, and only when the floor's DEFINITION changes -- a new
# inclusion rule, a different predictor transform, a different gene-set
# collection. Adding screens under the same rule does not change it; the
# content hash below is what distinguishes those.
ATLAS_VERSION = "1.0.0"

HEADER = '''"""Per-screen no-biology floors, embedded so a citation means one thing.

GENERATED FILE -- do not edit. Written by `src/build_atlas.py` from
`results/corpus/corpus_per_screen.csv`. `tests/test_cross_surface.py`
regenerates it and fails if this file differs, so it cannot drift from the
corpus it summarises.

WHAT A FLOOR IS. For one published screen, the share of the variance in its
gene-set hit ranking that is predicted by set size alone -- with no reference to
what any gene does. It is the value a method has to beat before any of its
ranking can be attributed to biology.

WHAT IT IS NOT. Not a quality score for a screen, not a criticism of the study
that produced it, and not a claim about any gene or gene set in it. A high floor
says the RANKING is largely recoverable from set construction; it says nothing
about whether the underlying experiment was well done. Where hits are counted
over the set's own members, a high floor is arithmetic before it is a confound
-- see scope limit 6 in the project README.

THE METHOD IS NOT NOVEL. EGAD shipped node-degree AUROC as a built-in null in
2017 (doi:10.1093/bioinformatics/btw695), Crow et al. PNAS 2019 did the
cross-dataset version, and GREAT (doi:10.1038/nbt.1630) corrects region-size
bias. What is here is the null computed identically across every screen and
made callable, not the idea of computing it.

Source data: BioGRID ORCS 2.0.18, human. Oughtred R et al., Protein Science
2021;30(1):187-200, doi:10.1002/pro.3978.
"""
from __future__ import annotations

ATLAS_VERSION = {version!r}

# sha256 of results/corpus/corpus_per_screen.csv, the table this was generated
# from. THIS is the stable identifier to cite: unlike a git commit it does not
# move when an unrelated file changes, and unlike a version string it cannot be
# bumped without the numbers actually changing.
SOURCE_SHA256 = {sha!r}

N_SCREENS = {n}
SOURCE = {source!r}
COLLECTION = {collection!r}
INCLUSION_RULE = {rule!r}
METHOD = {method!r}
LICENCE_NOTE = {licence!r}

# screen_id -> (r2_size_alone_log, r2_size_raw, n_hits, n_measured, n_sets_used,
#               pubmed_id)
# r2_size_alone_log is the headline floor: log10(1+hits) regressed on log10(size).
# r2_size_raw is the same on a raw-size predictor, carried because the choice of
# transform moves the number and nobody should have to trust ours.
FLOORS: dict[int, tuple[float, float, int, int, int, str]] = {{
{rows}
}}


def floor(screen_id) -> dict:
    """The no-biology floor for one screen in the atlas, with its provenance.

    Returns a dict carrying the number, how it was computed, what it is not, and
    the hash to cite. Returns a NOT_IN_ATLAS status rather than raising, because
    the caller is often an agent that renders a dict and buries a traceback.
    """
    try:
        key = int(screen_id)
    except (TypeError, ValueError):
        return {{"status": "NOT_IN_ATLAS", "screen_id": screen_id,
                "reason": "screen_id must be an integer BioGRID ORCS screen id."}}
    row = FLOORS.get(key)
    if row is None:
        return {{
            "status": "NOT_IN_ATLAS", "screen_id": key,
            "reason": (f"screen {{key}} is not among the {{N_SCREENS}} screens that "
                       f"met the inclusion rule. It may exist in BioGRID ORCS and "
                       f"have been excluded by the rule below, which is stated so "
                       f"you can check rather than guess."),
            "inclusion_rule": INCLUSION_RULE,
        }}
    r2_log, r2_raw, n_hits, n_measured, n_sets, pmid = row
    return {{
        "status": "IN_ATLAS",
        "screen_id": key,
        "no_biology_floor": r2_log,
        "no_biology_floor_raw_size_predictor": r2_raw,
        "n_hits": n_hits,
        "n_measured": n_measured,
        "n_sets_used": n_sets,
        "pubmed_id": pmid,
        "reading": (
            f"{{r2_log:.0%}} of the variance in this screen's gene-set hit ranking "
            f"is predicted by set size alone, with no reference to what any gene "
            f"does. A method claiming to find biology in this ranking has to beat "
            f"that before any of it is attributable."),
        "atlas_version": ATLAS_VERSION,
        "source_sha256": SOURCE_SHA256,
        "method": METHOD,
        "collection": COLLECTION,
        "source": SOURCE,
        "licence_note": LICENCE_NOTE,
        "cite": citation(),
        "what_this_is_not": (
            "Not a quality score for this screen and not a criticism of the study "
            "that produced it. It measures a property of the RANKING, not of the "
            "experiment, and it names no gene and no gene set."),
    }}


def citation() -> str:
    """The one string to put in a paper that reports a floor from this atlas."""
    return (
        f"denali no-biology floor atlas v{{ATLAS_VERSION}} "
        f"(sha256 {{SOURCE_SHA256[:16]}}), {{N_SCREENS}} human CRISPR screens from "
        f"BioGRID ORCS 2.0.18 (Oughtred R et al., Protein Science "
        f"2021;30(1):187-200, doi:10.1002/pro.3978), scored against "
        f"{{COLLECTION}}. https://github.com/alejandro-publius/denali"
    )
'''


def build() -> str:
    d = pd.read_csv(SRC).sort_values("screen_id")
    sha = hashlib.sha256(SRC.read_bytes()).hexdigest()
    rows = "\n".join(
        f"    {int(r.screen_id)}: ({r.r2_size_alone!r}, {r.r2_size_raw!r}, "
        f"{int(r.n_hits)}, {int(r.n_measured)}, {int(r.n_sets_used)}, "
        f"{str(r.source_id)!r}),"
        for r in d.itertuples())
    return HEADER.format(
        version=ATLAS_VERSION,
        sha=sha,
        n=len(d),
        source="BioGRID ORCS 2.0.18, human, screens meeting the inclusion rule",
        collection="MSigDB Hallmark v2026.1.Hs, 50 sets",
        rule=("HIT=YES count >= 20 and >= 10,000 genes measured; >= 8 usable "
              "sets, where a set is usable with >= 5 measured members"),
        method=("R^2 of log10(1+hits per set) on log10(set size), across the "
                "Hallmark sets within one screen"),
        licence=("Derived statistics only. The underlying screen data is BioGRID "
                 "ORCS's; cite doi:10.1002/pro.3978 alongside this atlas. "
                 "Descriptive curation (cell line, phenotype, library) is not "
                 "redistributed here -- it is in the research repository at "
                 "results/corpus/corpus_per_screen.csv."),
        rows=rows,
    )


def main() -> int:
    new = build()
    changed = (not OUT.exists()) or OUT.read_text() != new
    if "--check" in sys.argv:
        if changed:
            print("atlas.py is STALE — run: .venv/bin/python -m src.build_atlas")
            return 1
        print("atlas.py matches the corpus")
        return 0
    OUT.write_text(new)
    print(f"wrote {OUT.relative_to(ROOT)}  ({len(new)/1024:.0f} KB)"
          + ("" if changed else "  (unchanged)"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
