# Who this is for

Written 2026-08-16. **No user has been interviewed.** Everything below is desk
research and reasoning from what the tool actually does; the one place it touches
reality is the measurement in §2, which was run on a published screen rather than
imagined. Claims are marked **measured**, *researched*, or *speculation*, and the
speculation is not dressed up. "Biologists" is not a user and does not appear
below as one.

---

## 1. The moment, precisely

A pooled CRISPR screen finishes. Sequencing comes back, a hit caller (MAGeCK,
BAGEL2, drugZ) turns counts into a ranked list of thousands of genes, and usually
some enrichment step turns that into a ranked list of pathways. Somebody now picks
roughly three things to chase. Each costs about a year and six figures.

The decision is made in a meeting, from a table, in the two or three weeks after
the sequencing returns. That table is the artefact this tool reads. **Nobody in
that meeting has a way to ask how much of the table's ORDER is a property of how
the sets were built rather than of the biology** — and the honest answer on this
project's own screen was 46.5%.

That is the problem. Who has it is a narrower question than it looks.

---

## 2. The thing that must be said first, because it narrows everything

**Measured.** The confound this tool finds lives at the **pathway level**, not
the gene level.

Run on the RRA `gene_summary.txt` published with MAGeCKFlute (Liu lab, DFCI —
19,326 genes, a real genome-wide screen), the audit returns **R² 0.0067, NOT
SIZE-DOMINATED** — the 0.7th percentile of the reference distribution. The reason
is structural and will not go away: a pooled library gives nearly every gene the
**same number of guides** (17,116 of 19,326 genes have exactly four). Set size has
almost no variance at the gene level, so it cannot explain a gene ranking.
Contrast MSigDB Hallmark, where set sizes run 9 to 194 and size alone explains
46.5%.

Two consequences, and both are uncomfortable:

- **The "run it the moment your screen finishes" pitch is weaker than it sounds.**
  The MAGeCK, BAGEL2 and drugZ adapters remove the "I don't have that file"
  objection, which is real and worth removing. But the expected answer at the gene
  level is *not size-dominated*, and on a library with a fixed guide count per gene
  the tool now returns `UNDETERMINED` — the question could not be asked. That is
  useful (it rules a confound out, and almost nobody checks) but it is not the
  finding that makes someone change what they do.
- **The bite is after enrichment.** The audit gets its teeth when entries differ in
  size, which is what grouping genes into pathways creates. So the honest framing
  is *"before you act on the pathway table"*, not *"the moment the screen
  finishes"*.

**Measured, and a caution about the tool itself.** Testing on that real file also
found a way the tool can be wrong in the confident direction. Pooled libraries
pool every non-targeting guide into one control pseudo-gene — in this file
`NO_CURRENT`, with 979 guides where a real gene has four. On the full 19,326-row
screen it is harmless (R² 0.0067 with it, 0.0099 without). On a 130-row slice of
the *same file* it carries the fit: 0.4137 with, 0.0237 without, flipping the
verdict to CONFOUNDED. A tool whose argument is that rankings get carried by
arithmetic must not issue a verdict carried by one point in silence, so `audit()`
now reports the dependence and both numbers, and drops nothing. Anyone evaluating
this tool should try that themselves.

---

## 3. The candidate: a screening core facility

*Researched.* The strongest candidate is **not** an individual lab. It is a core
facility that runs pooled screens as a service and hands results back to other
labs. UC Berkeley has one at the Innovative Genomics Institute — the [Center for
CRISPR Target Discovery](https://innovativegenomics.org/center-for-crispr-target-discovery/),
a functional-genomics lab created by the IGI with the venture firm ATP, whose
stated scope runs the whole pipeline: experimental design, library construction,
screen execution, NGS prep, "as well as data processing and bioinformatic
analysis". Comparable facilities exist at Karolinska, the Max Planck Institute for
Biology of Ageing, Cancer Research Horizons (from ~£4,000 per genome-wide knockout
screen), and Greehey at UT Health San Antonio.

Why the core rather than the lab:

- **The deliverable is the artefact.** A core that ships bioinformatic analysis
  ships exactly the table this tool reads. The audit is a property of their
  product, so improving it is product work, not self-criticism.
- **Volume.** A core runs many screens for many groups. One integration pays off
  repeatedly; a lab that screens once a year gets one use out of the same effort.
- **The incentive points the right way.** For a core, "we ship a size-confound
  audit with every hit list" is a differentiator and a quality signal. For the
  scientist whose list is being graded, the identical output is an accusation.
- **They already own the analysis step.** They will not need convincing that set
  size and guide count are things a ranking can be made of; several core sites
  already discuss guide-efficiency bias in hit calling.

*Speculation, flagged:* I do not know whether any core currently reports any
construction-artefact diagnostic with its deliverable, and I have not asked one.
That is the first question to ask, and the answer changes the pitch completely —
if they already do, this is a feature request against an existing report, not a
new product.

---

## 4. The buyer is not the person being graded

This is the load-bearing observation and it is *inference*, not measurement.

Nobody wants to be told their hit list is 46% arithmetic. The scientist holding
the list has spent a year and a budget getting to it, has a paper shaped around
it, and has already chosen the three genes. A tool whose output is "the top of
your ranking is least able to justify itself" is asking that person to volunteer
for bad news, immediately before the moment they most need good news. **Expect
adoption from that person to be close to zero, and do not read their lack of
interest as evidence the measurement is wrong.**

The person who wants this is whoever bears the cost of the follow-up being wrong:

| Who | Why they want it | Why they might not |
|---|---|---|
| **Core facility director** | Reputation rides on the quality of what they hand back; a shipped audit is a differentiator | It grades their own deliverable; a bad number is awkward before it is useful |
| **PI allocating the next year of a postdoc's time** | Directly owns the year and the six figures | May not see the table until after the three genes are chosen |
| **Program officer / funder** | Pays for the validation that does not reproduce, at portfolio scale | Furthest from the file; needs it as a policy, not a command |
| **Industry target-selection group** | The cost of a wrong target is a program, not a paper | Most likely to have built something internal already |

*Speculation:* the funder route is the largest lever and the slowest. A single
core facility adopting it is the fastest evidence that it is worth anything.

---

## 5. What they do instead today

*Researched, and the honest answer is "surprisingly little that competes".*

- **Nothing.** The common case. The ranking is read as-is.
- **A secondary/targeted screen.** The field's standard advice above ~20 hits.
  This is the real competitor and it is much better evidence than this tool — it
  is also weeks of bench work and more money, which is precisely the commitment
  this check is meant to inform.
- **Guide-efficiency corrections at hit-calling time.** Published methods exist
  that reweight by guide activity. They address a different confound (guide
  quality) at a different level (per gene).
- **Competitive gene-set tests (CAMERA and relatives).** Genuinely address set
  size and inter-gene correlation, and denali's own `what_to_do` recommends them
  by name. **This tool does not replace them.** It is the cheap thing that tells
  you whether you need them, and `rerank` is a first approximation of the answer.

So the sales position is not "instead of a secondary screen". It is **"two minutes
before you commit to one"**.

---

## 6. Why they would change

The honest list is short:

1. **It costs almost nothing to try.** No install if they use the web page, no
   upload, no account, and it reads the file they already have. That is the entire
   reason the adapters and the browser version exist.
2. **It reports a percentile, not a bare statistic.** "Worse than nine in ten of
   1,272 published screens" is actionable in a way R² 0.46 is not.
3. **`rerank` gives them something to do.** A diagnosis with no treatment gets
   ignored. Naming which of their top ten cannot justify its position is a
   decision input.
4. **It grades its own authors first.** The study publishes its own screen at
   0.465 — atypically bad for the field — and says so. That is the only credential
   this has with someone who suspects a tool of flattering its makers.

## 7. Why they would not — the case against

Written because a document that only argues for itself is worthless.

- **The gene-level answer is usually "no problem here"** (§2). Someone who runs it
  at the moment their screen finishes, as we invite them to, most often learns
  nothing actionable.
- **It grades work already done.** There is no version of this that is not, in
  part, criticism.
- **The percentile's reference class is Hallmark.** Sets from Reactome, GO-BP or a
  bespoke collection have a different size distribution, so the percentile is
  indicative, not exact. The tool says so; a sceptic will still discount it.
- **The correction is a residual, not CAMERA.** `rerank` regresses log hits on set
  size and ranks by residual. It is defensible and simple; it is not the
  best-available size-aware test, and a statistician will say so.
- **Nobody is asking for this.** No inbound demand has been observed. The problem
  is real and measured; the *felt* need is unevidenced.

## 8. What would settle it

In rough order of cost, and none of it has been done:

1. Send the web page to one core facility director and watch whether they run it
   on a deliverable they have already shipped. One session answers more than this
   document does.
2. Ask whether any core already reports a construction-artefact diagnostic (§3).
3. Run the audit across many real published screens **at the pathway level** and
   report the distribution. The corpus arm did this against BioGRID ORCS at gene
   level; the pathway-level version is what the pitch actually rests on.
4. Find one case where `rerank` moved a real decision. Absent that, everything
   here is a plausible story about a measured effect.
