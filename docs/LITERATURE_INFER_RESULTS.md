# Reading the literature, rather than grepping it

Evaluation 11 asked whether 111 publications *mention* set size, using `grep`
over thirteen patterns, and its own output says a match is evidence of mention
and not of handling. **Evaluation 12 asked whether they did anything about it**,
with two different models reading each paper and disagreement reported as a
band. Pre-registered at
[`docs/LITERATURE_INFER_PREREG.md`](LITERATURE_INFER_PREREG.md) before a
single paper was classified.

**13.5–16.2% of publications adjusted for set size or measured it.** The band is
papers both models agreed on, to papers either model called; it is never
averaged and never broken by a third vote.

The headline share sits close to the regex's 18.0%, and **that closeness is two
errors nearly cancelling rather than two methods agreeing**:

- Of the 15 publications that actually did something, **10 matched none of the
  thirteen patterns** — mostly because they used GSEA, whose normalised
  enrichment score divides out set size without anyone saying the word "size".
- Of the 20 the regex called positive, **13 did nothing** — matches inside a
  LaTeX preamble, a competitive *binding* assay, a competitive *growth* assay.

The two methods agree on 5 papers out of a union of 25. **Most adjustment in
this literature is incidental**: it arrives bundled inside GSEA rather than as a
decision anyone made, which is a weaker thing than the field handling the
problem, and a different thing from the field ignoring it.

This is an estimate produced by a language model reading context windows, not
whole papers — `paperclip`'s parallel reader is gated and its `cat` truncates at
1,000 characters. That bounds recall and is disclosed as Correction 1 in the
pre-registration, appended before the first label existed. It writes
`results/literature_infer/` and never touches `results/frozen/`: no headline
here changes because a model said so.
