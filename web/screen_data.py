"""The eleven stages of a pooled CRISPR screen, and what denali can honestly say at each.

WHY THIS FILE EXISTS. denali arrives at stage 10 of 11. By then the library is
bought, the cells are transduced, the sequencing is paid for, and every decision
that determines whether the screen can work has already been made. Telling
someone their ranking is size-carried at that point is a post-mortem. The same
instrument could have said something useful at stage 2, and this is the data it
would say it from.

TWO RULES THIS FILE OBEYS AND THE PAGE INHERITS.

1. WHERE WE HAVE NOTHING, WE SAY SO. Most stages here get `runs=None`. A tool
   that pretends to be useful at every stage is not trusted at any of them, and
   the honest answer at stage 5 is "go do the bench work carefully, we cannot
   help you". Seven of the eleven stages say exactly that.

2. EVERY CLAIM CARRIES ITS VERIFICATION STATUS, not just its source. The
   design-first framing below was read from a primary source during the session
   that wrote this file. Several specific figures were NOT: the ScienceDirect
   review returns 403 to us, so the numbers attributed to it are carried from
   the brief that commissioned this work rather than checked. Those are marked
   `verified=False` and the page renders them differently. A tool whose whole
   argument is that unverified numbers get believed cannot ship unverified
   numbers silently.

The corpus reference classes are computed here from the committed per-screen
table rather than typed, so they cannot drift from it.
"""
from __future__ import annotations

import pathlib

import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parent.parent
CORPUS = ROOT / "results" / "corpus" / "corpus_per_screen.csv"

# Primary source, opened and read at build time by the session that wrote this.
# The quoted framing below is verbatim from it.
DESIGN_SRC = "https://www.cd-genomics.com/biomedical-ngs/resource/pooled-crispr-screen-design.html"
# Returns HTTP 403 to us. Everything attributed here is carried, not checked.
REVIEW_SRC = "https://www.sciencedirect.com/science/article/pii/S1046202326001118"

COUPLED = ("MOI, coverage (representation), biological replicates, and the "
           "readout window")


def _claim(text, source, verified, note=""):
    return {"text": text, "source": source, "verified": bool(verified),
            "note": note}


UNCHECKED = ("Carried from the design literature via the brief that commissioned "
             "this page. We could not open a primary source for this figure — "
             "the review returns 403 to us. Treat it as orientation, not a "
             "specification, and check it against your own core facility.")

# Every stage. `runs` is what denali can actually do here, and None is the
# common and honest case.
STAGES = [
    {
        "n": 1, "key": "question", "title": "The question",
        "decides": "What you are actually looking for, and what would count as "
                   "finding it. Everything downstream is a consequence of this "
                   "sentence.",
        "matters": ["What phenotype separates the cells you want from the ones "
                    "you do not?",
                    "What selection turns that phenotype into survival, "
                    "fluorescence, or a sortable signal?",
                    "What result would make you abandon the hypothesis?"],
        "breaks": "A screen with no clear answer to the third question can only "
                  "confirm what you already believed. There is no analysis that "
                  "repairs that later.",
        "checklist": ["The phenotype is written down in one sentence",
                      "The selection that reads it out is chosen",
                      "I have written what would count as a hit",
                      "I have written what would make me stop"],
        "runs": "prereg",
        "claims": [],
    },
    {
        "n": 2, "key": "format", "title": "Format",
        "decides": "Pooled or arrayed, knockout or CRISPRi/a, genome-wide or "
                   "focused. This fixes the cost and the kind of answer you can "
                   "get.",
        "matters": ["Pooled is cheap per gene and gives you a ranking; arrayed "
                    "is expensive and gives you a measurement per gene.",
                    "Knockout removes the protein; CRISPRi reduces it. If your "
                    "gene is essential, knockout may just kill the cell.",
                    "A focused library asks a sharper question of fewer genes."],
        "breaks": "Choosing genome-wide when you needed arrayed means a ranking "
                  "where you needed a number, and you will not find that out "
                  "until stage 10.",
        "checklist": ["Pooled vs arrayed decided, with the reason written down",
                      "Knockout vs CRISPRi/a decided",
                      "Library scope decided"],
        "runs": "floor",
        "claims": [],
    },
    {
        "n": 3, "key": "library", "title": "Library",
        "decides": "Which guides target which genes, and how many per gene.",
        "matters": ["Guides per gene is the number that decides whether one bad "
                    "guide can carry a gene.",
                    "A library with known performance beats a novel one unless "
                    "you have a reason."],
        "breaks": "With too few guides per gene, a single guide that cuts badly "
                  "or cuts somewhere else decides that gene's fate. You cannot "
                  "tell that apart from biology afterwards, because there is "
                  "nothing to compare the guide against.",
        "checklist": ["Library chosen and its guides-per-gene known",
                      "Non-targeting and positive controls present in the pool",
                      "Library representation confirmed after amplification"],
        "runs": None,
        "runs_note": "Nothing to run. denali reads results, and there are none "
                     "yet. Choosing the library well is bench and ordering work.",
        "claims": [_claim("3–6 sgRNAs per gene is the usual range; below about "
                          "3–4, single-guide variability starts to dominate the "
                          "gene-level call.", REVIEW_SRC, False, UNCHECKED)],
    },
    {
        "n": 4, "key": "packaging", "title": "Packaging",
        "decides": "Turning the library into virus, and knowing its titre.",
        "matters": ["Titre has to be measured in the cells you will screen, not "
                    "assumed from another line."],
        "breaks": "An unmeasured titre means you cannot set the next stage's "
                  "MOI, which is the stage that decides whether the screen is "
                  "interpretable at all.",
        "checklist": ["Virus produced", "Titre measured in the screening line"],
        "runs": None,
        "runs_note": "Nothing to run. This is wet-lab work and denali has no "
                     "opinion on it.",
        "claims": [],
    },
    {
        "n": 5, "key": "transduction", "title": "Transduction",
        "decides": "How many guides end up in each cell.",
        "matters": ["Multiplicity of infection is set here and cannot be "
                    "changed later.",
                    "It trades off against how many cells you have to grow."],
        "breaks": "If cells take up more than one guide, you cannot tell which "
                  "guide caused what you measured. Two genes are knocked out in "
                  "the same cell and the phenotype belongs to neither of them "
                  "in particular. Nothing downstream repairs this — not a better "
                  "hit-caller, not more replicates, not denali.",
        "checklist": ["MOI chosen and written down",
                      "Transduction efficiency measured, not assumed",
                      "Selection confirms the intended proportion survived"],
        "runs": None,
        "runs_note": "Nothing to run, and this is the stage where that matters "
                     "most. Get it right at the bench; there is no analytical "
                     "rescue.",
        "claims": [_claim("A low MOI — commonly quoted around 0.3 — is used so "
                          "most transduced cells carry a single guide. Improper "
                          "MOI is described as the most common and most "
                          "consequential pitfall in pooled screening.",
                          REVIEW_SRC, False, UNCHECKED),
                   _claim(f"Treat {COUPLED} as ONE coupled decision rather than "
                          "four separate ones.", DESIGN_SRC, True,
                          "Read verbatim from the source at build time.")],
    },
    {
        "n": 6, "key": "coverage", "title": "Coverage",
        "decides": "How many cells you carry per guide, at every step.",
        "matters": ["Coverage has to hold through transduction, selection and "
                    "every passage — the bottleneck is whichever step is "
                    "narrowest.",
                    "It is the main defence against drift."],
        "breaks": "Below adequate coverage, which guides are present at the end "
                  "is decided partly by chance rather than by your selection. "
                  "The screen still produces a ranked list. It just is not "
                  "about your phenotype.",
        "checklist": ["Cells-per-guide chosen for every step, not just the start",
                      "The narrowest step identified",
                      "Enough cells actually harvested at each passage"],
        "runs": None,
        "runs_note": "Nothing to run. Coverage is a cell-counting decision.",
        "claims": [_claim("Representation is commonly planned in the 200–1000× "
                          "cells-per-guide range, with around 800× reported as "
                          "scoring best in one comparison (AUC 0.82).",
                          REVIEW_SRC, False, UNCHECKED)],
    },
    {
        "n": 7, "key": "selection", "title": "Selection",
        "decides": "The pressure that separates the cells you care about.",
        "matters": ["Selection strength is the difference between a signal and "
                    "a flat result.",
                    "A pilot at several doses costs far less than a failed "
                    "screen."],
        "breaks": "Too little pressure and nothing separates: every guide "
                  "survives, the counts barely move, and the screen returns a "
                  "ranking of noise. This is a common reason a screen 'finds "
                  "nothing'.",
        "checklist": ["Selection agent and dose piloted, not guessed",
                      "A positive control moves under this pressure",
                      "An untreated arm is carried alongside"],
        "runs": None,
        "runs_note": "Nothing to run yet.",
        "claims": [_claim("Insufficient selection pressure is a common reason a "
                          "screen returns no enrichment.", REVIEW_SRC, False,
                          UNCHECKED)],
    },
    {
        "n": 8, "key": "window", "title": "Readout window",
        "decides": "How long the cells grow under pressure before you harvest.",
        "matters": ["Too short and the effect has not accumulated; too long and "
                    "the fittest cells take over regardless of your phenotype."],
        "breaks": "A window chosen for convenience turns a phenotype screen into "
                  "a proliferation screen, and the top of your list becomes "
                  "essential genes.",
        "checklist": ["Timepoint chosen with a reason",
                      "An early reference sample banked for comparison"],
        "runs": None,
        "runs_note": "Nothing to run.",
        "claims": [_claim(f"The window is one of the four coupled decisions: "
                          f"{COUPLED}.", DESIGN_SRC, True,
                          "Read verbatim from the source at build time.")],
    },
    {
        "n": 9, "key": "sequencing", "title": "Sequencing",
        "decides": "Turning surviving cells into guide counts.",
        "matters": ["How much gDNA you take in decides how much of your library "
                    "you actually sampled.",
                    "Read depth past a point buys almost nothing."],
        "breaks": "Sequencing deeply from too little input DNA measures the same "
                  "few molecules repeatedly. The counts look precise and are not.",
        "checklist": ["gDNA input covers the intended representation",
                      "Guide PCR kept in linear range",
                      "Read depth planned per guide, not per sample"],
        "runs": None,
        "runs_note": "Nothing to run until the counts exist.",
        "claims": [_claim("Beyond roughly 25 reads per guide, additional depth "
                          "adds little; more guides at lower depth is generally "
                          "preferred to fewer guides sequenced deeply.",
                          REVIEW_SRC, False, UNCHECKED)],
    },
    {
        "n": 10, "key": "calling", "title": "Hit calling and enrichment",
        "decides": "Which genes are hits, and what the hits are about.",
        "matters": ["The hit-caller you choose changes the answer.",
                    "Enrichment turns a gene list into a pathway story, and that "
                    "is the step where set construction enters."],
        "breaks": "A gene-set ranking can be largely explained by how big the "
                  "sets are rather than by what the genes do. Bigger sets return "
                  "more hits whatever the biology, so the top of your pathway "
                  "list can be an artifact of the collection you chose.",
        "checklist": ["Hit-caller chosen, with the direction stated",
                      "Enrichment run against a named collection",
                      "Ranking audited for set-size confounding",
                      "Pre-registration compared against the result"],
        "runs": "audit",
        "claims": [_claim("Normalisation choice materially changes which hits "
                          "you get: median-centring has been reported to give "
                          "around 34% hit overlap between screens where better "
                          "normalisation gives around 84%.", REVIEW_SRC, False,
                          UNCHECKED)],
    },
    {
        "n": 11, "key": "validation", "title": "Validation",
        "decides": "Which candidates you spend a year and six figures on.",
        "matters": ["This is the decision every earlier stage was serving.",
                    "The entries a size-aware correction demotes are the ones "
                    "your ranking is least able to justify."],
        "breaks": "Validating a candidate whose rank came from set size costs "
                  "the same as validating a real one and returns nothing.",
        "checklist": ["Top entries checked against the size-aware re-ranking",
                      "Pre-registration re-read before choosing",
                      "Candidates chosen for reasons written down"],
        "runs": "rerank",
        "claims": [],
    },
]

# What denali offers, by key. Anything not listed is honestly nothing.
TOOLS = {
    "prereg": {"label": "Write your pre-registration",
               "what": "Write down now what would count as a hit and what would "
                       "make you stop. It is hashed and timestamped in this "
                       "browser, and shown back to you at stage 10."},
    "floor": {"label": "Estimate your construction floor",
              "what": "See where screens shaped like the one you are planning "
                      "have landed, before you spend anything."},
    "audit": {"label": "Audit your ranking",
              "what": "Measure how much of your ranking is explained by how the "
                      "sets were built."},
    "rerank": {"label": "See what the correction moves",
               "what": "Apply the size correction and see which of your top "
                       "entries do not survive it."},
}


def reference_classes() -> dict:
    """Empirical floors of published screens, grouped by how many hits they returned.

    NOT A PREDICTION, and the page must not render it as one. Evaluation 13 in
    this repository tried to predict a screen's floor from four design variables
    and reached a cross-validated R^2 of 0.0935 against a pre-registered 0.20
    threshold -- it does not work. So this returns a DISTRIBUTION over similar
    published screens, and the spread is the message: inside every bin below the
    p10-to-p90 range is wider than the gap between the bins' medians. What a
    planner can be told is what is typical and what would be unusual; what they
    cannot be told is where their own screen will land.
    """
    d = pd.read_csv(CORPUS)
    bins = [(20, 100), (100, 500), (500, 2000), (2000, 10 ** 12)]
    out = []
    for lo, hi in bins:
        s = d[(d.n_hits >= lo) & (d.n_hits < hi)]["r2_size_alone"]
        if len(s) < 8:            # too few to say anything, and we say so
            out.append({"lo": lo, "hi": None if hi > 10 ** 11 else hi,
                        "n": int(len(s)), "enough": False})
            continue
        out.append({
            "lo": lo, "hi": None if hi > 10 ** 11 else hi, "n": int(len(s)),
            "enough": True,
            "p10": round(float(s.quantile(0.10)), 4),
            "p50": round(float(s.median()), 4),
            "p90": round(float(s.quantile(0.90)), 4),
            "spread": round(float(s.quantile(0.90) - s.quantile(0.10)), 4),
        })
    return {
        "bins": out,
        "n_screens": int(len(d)),
        "collection": "MSigDB Hallmark",
        "min_similar": 8,
    }
