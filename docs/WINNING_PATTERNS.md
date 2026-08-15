# Winning patterns — ACTIVE design DNA

Distilled from prior winning hackathon projects. These are **intentional design
choices for this project**, not history. The raw scouting notes are archived; the
mechanics live here.

---

## 1. KScope — mechanistic interpretability

**Do not stop at correlation.** A gene that correlates with disease is a
hypothesis, not a driver.

Applied here: once drivers are prioritised, test whether they survive a
**computational intervention** — public perturbation / CRISPR evidence showing
the driver moves the disease program. Association and mechanistic evidence are
labelled differently and never conflated.

*Status: deferred until a replicated program exists.*

## 2. Spatial Awareness — the discovery arc

```
raw biological data → biological state → independent validation
  → hypothesis → computational experiment → new result
```

Applied here verbatim: lung atlas → cell state/program → 582-lung replication →
driver hypothesis → perturbation test → result. **Independent validation sits
before the hypothesis, not after it.** That ordering is the cheapest credibility
in the whole set.

## 3. Discordance — expose the evidence, including against yourself

Every major conclusion must expose: **source data, provenance, conflicting
evidence, uncertainty, and abstention when evidence is weak.**

Applied here: full DE tables are saved, not just significant rows; parsing traps
and confounders are recorded beside the results; the pre-registered n being wrong
by 44% is written down rather than restated; and "not established" is a
permitted, non-embarrassing answer.

## 4. Glioblasters / SpaceAix — show actual biological artifacts

Show **UMAPs, donor-level distributions, gene programs, pathway enrichment,
effect sizes, validation plots, outcome curves, perturbation results.**

**Avoid generic AI dashboard cards.** A donor-level paired plot with 21 real
people on it beats any KPI tile. The current `figures/discovery/` figure is
deliberately of this kind — it shows the null honestly rather than hiding it.

## 5. AgentSeer — inspectable process graph

The eventual interface — **only after the biology survives** — exposes the
research workflow as a graph where **clicking a node reveals the actual dataset,
result or evidence behind that conclusion.** Not a chat window, not a report.

*Status: explicitly not built. See `CLAUDE.md` §9.*

## 6. EvoCapsid / GenPlasmid — finish with a concrete artifact

End with a **scientific object**, not a document: a validated disease program, a
ranked driver list, a reproducible analysis, a perturbation result, a reusable
dataset or benchmark, or a biological hypothesis backed by external evidence.

**Do not end with a report or a chatbot answer.**

---

# Event-specific evidence, added 2026-08-14

> **Provenance note.** The four items below were supplied by the user on
> 2026-08-14 and are recorded as given. They were **not independently verified
> this session** — no prior-art sweep was run, per standing prohibition. Treat
> the factual claims as user-sourced; treat the implications as design decisions
> already taken.

## 7. Arc Virtual Cell Challenge 2025 — and Arc co-hosts this event

- **Hybrid deep learning + classical statistical features beat pure neural
  approaches.**
- **Pseudobulk representations carried most of the usable signal.**
- The winner was ranked by **average rank across seven metrics**, not by one.

**Implication, already acted on:** our scoring step is pseudobulk + classical
statistics, which *matches the co-host's own published finding* rather than
fighting it. And we **report several metrics, not one headline number** — a
single reversal score presented alone would contradict the evidence from the
people judging us.

## 8. Bio x AI Hackathon — $125K, 11 winning teams

**MCP servers won repeatedly:** Holy Bio MCP ($10K), Protein Bank MCP ($10K),
PDB-MCP at midpoint.

**Implication:** `HACKATHON_PLAN.md` step 9 — exposing the scored matrix as an
MCP server — is not a nice-to-have. It is a **proven winning artifact** at this
event's own format, and it is the piece that makes the result reusable by
someone else.

## 9. Owkin "Rewiring Biology" — the honesty result

- **KScope won 1st** on a **frozen model with no retraining.**
- **Discordance won 2nd** by **surviving live adversarial questioning** rather
  than confabulating.
- **Spatial Awareness won 3rd**, credited for answers that **went beyond the demo.**
- Owkin's own stated takeaway: **convergence on AI that is honest about the
  limits of its evidence.**

**Implication — this is the headline, not a design requirement.** We already
have what these three won on, and it is not something we need to build:

- a **preserved null** (the ILD project, retired on its own pre-registered
  evidence rather than rescued), and
- **fired kill criteria** with hashes proving the thresholds preceded the data
  (`GATE_C1_PREREGISTRATION.md`, `d7d90e41…`), and
- **three of four programs failed** at the gate and were not revisited.

Lead with that. Most teams cannot show a result they killed.

## 10. MorphoLogic AI — sponsor-specific data prize at Bio x ML

**Implication:** the additional awards beyond the three track prizes are a
**second, less contested shot.** Track A is the most crowded track here
(`HACKATHON_PLAN.md` risk 3), so sponsor-specific prizes are worth explicit
targeting — Benchling, Modal, Biohub and Tamarind all appear in our pipeline
already.

---

## 11. The general principle

> **Actual biological result > agent theatrics.
> External evidence > model self-evaluation.
> Interesting scientific artifact > generic product polish.**

## Anti-patterns, measured

- **An LLM judging an LLM is not validation.** The host's own figure: 86% of
  deliberately-opposed analyses passed AI review.
- **Re-deriving the organiser's published result in front of them.** Foreclosed
  for this project: no H&E, no pathology foundation model, no expression-from-
  histology, no MSI-from-H&E, no colorectal cancer, no agentic research copilot.
- **No biological object.** 8 of 9 studied winners held a tissue, protein,
  receptor, capsid or plasmid. Output a **named thing**, not a percentage.
