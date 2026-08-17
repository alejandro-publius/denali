# Expansion pre-registration — the null behind the floor

**Committed before the values it decides.** Written 2026-08-17 at `c7f528a`, tree
clean, no other session's work in flight.

---

## 0 · Orientation, and what the reading changed

Twenty lines, as required, and they are not a summary — they are the four things
the reading changed about what I was going to do.

1. `README.md` scope limit 6 is not a caveat on one arm, it is a precondition on
   the whole instrument: where `hits` are counted over the set's own members, a
   large R² is arithmetic and the correct null is binomial, not zero.
2. `README.md` findings: eleven evaluations, seven negative, and evaluation 10
   (the 1,272-screen corpus) is published across several surfaces.
3. `docs/METHOD_RULES.md` — "know what your test can and cannot return… if you do
   not compute [floor and ceiling] first you will interpret an artifact."
4. `docs/METHOD_RULES.md` Evidence — a check is not evidence until it has been
   observed to fail; mutate the guard's inputs as well as its subject.
5. `docs/LIMITATIONS.md` §0 is a collapse the project found in itself.
6. `results/breadth/README.md` is the boundary condition on our own tool, and it
   is the document that redirected this session.
7. It reports the corpus arm **has** counting structure — `src/corpus_audit.py`
   sets hits = set members that were hits, so `hits ≤ size` in every screen.
8. It states that on a 250-screen sample the observed median R² is 0.19 against a
   binomial null median of 0.79, above its own null in only 6% of screens.
9. It explicitly leaves the interpretation uncorrected: "a decision for the
   author, not a side effect of an exploratory probe."
10. `benchmarks/challenge/board.md` — our own correction placed 4th of 4 against a
    size-contaminated target and 1st against a size-corrected one.
11. So the project already knows a metric's target decides its winner. That is the
    same shape as the problem below, one level out.
12. **What the reading changed:** I was going to audit external models (Track 1).
13. Instead: the claim in item 8 has **no committed artifact**.
    `results/breadth/null_baselines.py` has four arms — primary, metabolites,
    microbiome, regions — and no corpus arm. The number is prose only.
14. It is also the most consequential claim in that document, because it is the
    one that says how `denali floor` should be read.
15. `denali floor` ships in a pip-installable package and prints, for any of 1,272
    screens: *"A method claiming to find biology in this ranking has to beat that
    before any of it is attributable."*
16. If item 8 is right, that sentence points the wrong way: no-biology for a
    counting mapping is **higher** than the number being printed, not lower.
17. The raw ORCS substrate is gitignored and absent, so item 8 cannot be
    reproduced here and I will not estimate it. An estimated row is fraud.
18. But the same proposition is exactly testable on data that **is** committed:
    seven real published screens in `audits/external/*/std.csv`, per-set.
19. That is what this pre-registration governs.
20. Nothing below writes to `results/frozen/`. No gene, gene set, publication or
    author is named as a finding anywhere in this arm.

---

## 1 · The question

For a published gene-set enrichment ranking with **counting structure**
(`hits ≤ size`, both counted over the same members), does the observed size-alone
R² clear the binomial no-biology null for that same mapping?

This decides whether `denali floor`'s instruction to "beat that" is sound.

## 2 · The data, fixed before running

The seven standardised external screens committed at `audits/external/*/std.csv`:
`batf3`, `gastric`, `htra3-hnscc-gokegg`, `smarca4_ala`, `tau_lrp1`,
`yak-pasmc-s007`, `zga_crispra`. Every one is a real published supplementary
table whose hit column was verified against the source document.

Inclusion: a screen enters if it parses through `denali_audit.adapters.detect()`
and has at least `MIN_SETS` (8) rows. No screen is excluded for its result. If a
screen turns out not to have counting structure it is **still reported**, in its
own row, labelled — it is evidence about the mapping, not a reject.

## 3 · The method, fixed before running

`results/breadth/null_baselines.py::null_baseline()`, unmodified and imported
rather than copied. It is the function that produced the published null column for
the other three domains, so this arm is scored by the same code.

Counting structure is determined by that function's own `has_counting_structure`
/ `frac_hits_le_size` output, not by my judgement.

## 4 · The decision rule, fixed before seeing any value

A screen **clears its null** if its observed R² exceeds the upper bound of the
null's 95% interval.

- **If ≥ 5 of 7 clear:** the breadth arm's corpus reading does not generalise to
  these screens, `denali floor`'s wording is defensible as written, and I report
  that the concern was unfounded — prominently, in the same place I would have
  reported the defect.
- **If ≤ 3 of 7 clear:** the instruction shipped by `denali floor` is a defect. It
  becomes a scope limit the same day, and the tool says so on its own output
  rather than in a footnote in a doc.
- **If exactly 4 clear:** the result is indeterminate at this n. I report it as
  indeterminate and do not round it toward either conclusion.

## 5 · What would make this arm wrong

- **n = 7.** Seven screens cannot settle a claim made about 1,272. This arm can
  corroborate or fail to corroborate the breadth reading on data I can actually
  run; it cannot reproduce the 250-screen figure and does not claim to.
- **The binomial is the simplest defensible null, not the only one.** A per-member
  hit rate that genuinely varies with set size would move the baseline. The
  breadth arm states this limitation and it applies here unchanged.
- **These seven were selected for the external gallery**, on the criterion that
  their hit column was a true per-set count. That is not a random sample of the
  literature and the direction of any bias is unknown.
- **Estimand mismatch.** `atlas.py`'s floor uses a log-size predictor; this arm
  reports whichever the null function uses, and both are printed.

## 6 · What this does not do

It does not correct evaluation 10, and it does not touch `results/corpus/` or
`results/frozen/`. It does not claim any screen is bad, any ranking is wrong, or
any published conclusion is unsupported. It measures a property of a mapping.
