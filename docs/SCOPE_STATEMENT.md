# Scope statement

**This goes on screen. Not in an appendix.**

---

> ## Guide-pair concordance is −0.019.
>
> ## Independent guides targeting the same gene do not agree, so gene-level calls are not reproducible in this data. We make pathway-level claims only and name no novel gene.
>
> ## SREBF2 appears as a recovered known answer validating the ranking, not as a discovery.

---

## Why we are saying this ourselves

The Replogli library targets 738 genes with two independent guide constructs
(`P1`, `P2`) scored as separate rows. If our per-gene score were reliable, the
two rows for one gene would agree. They do not:

| Subset | n | Spearman ρ |
|---|---:|---:|
| All guide-pair genes | 738 | **−0.019** |
| \|u_z\| > 1.5 in either | 339 | −0.001 |
| \|u_z\| > 2.0 in either | 190 | +0.029 |
| \|u_z\| > 2.5 in either | 93 | +0.048 |
| \|u_z\| > 3.0 in either | 43 | −0.076 |

Flat at every effect-size threshold. This is **not** a power artifact that
disappears in the strong hits.

## What survives, and why

Aggregate and pathway-level signal is real and separately evidenced:

- the pre-committed **nonsense program returns 0 hits** at q<0.05 versus 517 and
  773 for the real programs — the method does not invent signal;
- **11 of 17 canonical pathway members land in the extreme 10%** of a
  9,837-gene ranking, binomial **p = 7.0 × 10⁻⁸**;
- **sign correctness is 11/14 = 79%** across both tails.

A score too noisy to rank one gene against its neighbour can still place a whole
pathway at the extremes. **Pathway-level is the level this data supports.**

## The rule this imposes on every output

1. **No novel gene is named** in any table, figure, label, slide or spoken line.
2. Named genes appear **only** as recovered known answers, and are labelled as such.
3. Any ranked list shown must carry the concordance number.
4. `rpe1_covered = False` renders as **NOT CHECKED**, never as a blank or a pass.
5. Claims are phrased about **the pathway**, not about an individual gene.

## Evidence-layer concentration — disclosed, not discovered

We cannot fix literature coverage tonight, so we quantify it.

| | Paperclip | Europe PMC |
|---|---:|---:|
| Genes with a source | 113 | 113 |
| Distinct sources | **34** | 75 |
| **Sources per gene** | **0.30** | 0.66 |
| **Max share held by one source** | **50.4%** (57 of 113 genes) | 8.9% (10 genes) |
| Sources used for exactly one gene | 25 | 58 |
| **Genes resting on exactly one source** | **113 — all of them** | 113 |
| Top-hit year range | 2024–2026 only | 2000–2025 |

One review, `PMC12242609` (*"When Proteins Go Berserk: The Unfolded Protein
Response and ER Stress"*), is the cited evidence for **57 of 113 genes**. Only
**14 of 113** top hits name their gene in the title.

**Interpretation.** One-shot semantic retrieval returns *a recent review that
plausibly mentions the gene*, not the evidence establishing its role. ATF6's
foundational literature is from ~2000; the top hit returned for ATF6 is a 2025
hearing-and-vision-loss paper.

**Therefore: the evidence layer is a pointer layer, not a per-gene evidence
chain, and must not be described as one.** The fix is citation chaining
(`paperclip citation-explorer`), not a larger one-shot query. Not done.

These numbers are machine-readable in
`results/frozen/provenance.json → evidence_source_concentration`.

---

*A judge who spots a weakness and finds we reported it first is a judge we have
already won.*
