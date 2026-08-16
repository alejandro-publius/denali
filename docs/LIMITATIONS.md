# Limitations

A first-class document. Everything here weakens our own result, and all of it was
found by us before anyone asked.

---

## 0. ⚠ THE HEADLINE MAY SUBSTANTIALLY REDUCE TO "LARGER GENE SETS RETURN MORE HITS"

**Post-freeze sensitivity check, not pre-registered. Run after an adversarial
self-critique named this as our weakest point. It was not in the plan.**

Three of our six "measurability" features are properties of **how the gene set
was constructed**, not of measurement. We split them:

| Model | features | adj R² |
|---|---:|---:|
| All six — **the pre-registered primary** | 6 | **0.751** |
| Outcome-independent five | 5 | 0.561 |
| **Measurement only** (`expr_ratio`, `sd_ratio`, `essentiality_density`) | 3 | **0.152** |
| **Set construction only** (`n_present`, `frac_present`, `coherence`) | 3 | **0.697** |
| Set size alone | 1 | 0.465 |

**The finding is carried by set construction, not by measurement.** Set size by
itself beats all three measurement features combined, three times over.

**We attributed the variance to the wrong thing.** The corrected reading is that
how many knockdowns appear to move a program is mostly a function of **how the
program was defined — chiefly how many genes are in it** — rather than how well
those genes were measured, and not of the program's biology.

The pre-registered range 0.561–0.751 **stands as reported** and is not revised;
what changes is the word *"measurement"* in its interpretation. Better
instrumentation would not move this number, because the dominant term is a
property of the gene-set catalogue.

Full record: `results/sensitivity/README.md`.

## 1. The headline number is partly mechanical — 0.561, not 0.751, is the floor

The deciding statistic is adjusted R² of program reversibility on six
measurability features: **0.751**.

**One of those six, `coherence`, is computed from the same matrix `X` as the
outcome `R_p`.** A program whose members move together across perturbations will
by construction produce a stronger aggregate signal. Part of the fit is therefore
arithmetic, not discovery.

| Model | Adjusted R² |
|---|---:|
| All six features | 0.751 |
| **Outcome-independent features only** | **0.561** |

**We report the range 56%–75% everywhere, not the top of it.** The pre-registered
decision used all six because that is what was written before the sweep, and we
did not revise it once the numbers were visible. But 0.561 is the number that
survives the circularity objection, and anyone quoting 0.751 alone is quoting us
incorrectly.

## 2. Gene-level calls are not reproducible — guide-pair concordance is −0.019

The Replogle library targets 738 genes with two independent sgRNA constructs
scored as separate rows. If our per-gene score were reliable those rows would
agree. They do not:

| Subset | n | Spearman ρ |
|---|---:|---:|
| All guide-pair genes | 738 | **−0.019** |
| \|u_z\| > 1.5 in either | 339 | −0.001 |
| \|u_z\| > 2.0 in either | 190 | +0.029 |
| \|u_z\| > 2.5 in either | 93 | +0.048 |
| \|u_z\| > 3.0 in either | 43 | −0.076 |

Flat at every effect-size threshold — not a power artifact that resolves in the
strong hits.

**Consequence, enforced throughout: pathway-level claims only, and no novel gene
is named anywhere in this project.** SREBF2 appears solely as a recovered known
answer validating the ranking. The per-gene divergence table was **deleted** from
the frozen interface for this reason and replaced with program-level counts.

## 3. One cell line, unstimulated

Everything is K562: leukemia-derived, proliferating, unstressed. Two direct
consequences:

- **Program A's null is conditional, not biological.** Unstimulated K562 has no ER
  stress, so the unfolded protein response was never engaged. Knocking out the
  sensors of an alarm that is not ringing moves nothing. Our Gate C1 tested
  whether the program was *measurable*; it should have tested whether it was
  *engaged*. That distinction was missing from the pre-registration.
- **Nothing here transfers to another cell type without re-running.** The RPE1 arm
  covers 24.2% of our knockdowns, and 94.1% of essential genes versus 11.3% of
  non-essential ones — so it can only check the genes our toxicity filter already
  flags.

## 4. The measurability gate is wrong 20 times out of 50

We built the gate anyone would build. Across 50 programs:

- **20/50** fail the gate and still produce hits
- **1/50** passes the gate and produces zero hits
- the **held-out** program fails the gate (`expr_ratio` 0.92) and ranks **11/50**
  with 773 hits

**Our own filter would have discarded our best result.** We report this rather
than quietly dropping the gate, and we only found it by scoring every program rather
than the ones the filter approved.

## 5. The evidence layer is a pointer layer, not an evidence chain

Paperclip was authenticated and used for one citation per gene across 113 genes.
We then audited it instead of trusting it:

| | |
|---|---:|
| Distinct sources covering 113 genes | **34** |
| Largest share held by one review | **50.4%** (57 genes) |
| Top hits naming their own gene in the title | **14 / 113** |
| Blind 20-gene probe returning the same zebrafish methods paper | **19 / 20** |
| Blind probe returning a paper about a *different* gene | **1** |

The clearest single failure: **our top-cited source for ATF3 was a paper about
integrating single-cell transcriptomic data across species.** It has nothing to do
with ATF3.

**Do not describe this project as producing a per-gene evidence chain.** It
produces a per-gene pointer to a recent review. The fix is citation chaining, not
a larger one-shot query, and we did not build it.

## 6. The held-out evaluation is underpowered and one axis failed

Ten Reactome programs, chosen by public rule and not scored until
the predictor was hashed.

- **Only 1 of 10 passes the measurability gate** → pre-registered rule fires:
  **UNDERPOWERED AND INCONCLUSIVE**.
- Axis 1, rank recovery: ρ = +0.526, **95% CI [−0.101, +0.913]** — crosses zero.
  **PARTIAL**.
- Axis 2, binary recovery: balanced accuracy **0.4375**, **worse than chance**,
  **zero true positives**. **FAILURE**.
- Worst miss: the program with the **highest** prediction (R_p 5.26) returned
  **0 hits**.

**We did not refit.** The pre-registration forbids it; the commit history proves
we didn't.

## 7. Disclosed process failures

- **We published the essentiality coefficient with the wrong sign.** It is
  **−0.021**, not +0.021. The magnitude and the p-value (0.90) were right and the
  conclusion — essentiality does not predict program-level reversibility — is
  unaffected, but the sign was wrong in four documents. **Caught by
  `tests/test_frozen_invariants.py`, which asserts the value against
  `provenance.json` rather than against our memory.**
- **We said "three of seven controls are FAIL."** It is **four** of seven, plus
  one CAVEAT. Also caught by the test suite.
- **We reported Proto as broken based on a package name Proto does not publish.**
  Our note read `pip install proto-language` → fails at import. Proto is Evo
  Design's generative-biology infrastructure, and `proto-language` is an unrelated
  package; we had tested a name collision and recorded the result as Proto's
  status. The real install —
  `pip install git+https://github.com/evo-design/proto-tools.git` — **succeeds**,
  and `proto-tools doctor` exits 0. Two things are wrong here and both are ours:
  we published a failure we had not attributed correctly, and it is the same error
  class as the `sundial` name collision we had already caught and warned about in
  the same document. **We found and corrected this ourselves.** The corrected
  status is INSTALLED, NOT USED.

- **The "21-minute gap" was filesystem mtime, not git.** `score_k562.py` was
  *created* on disk at 08:45:15 but first *committed* at 08:52:32. Git stores the
  latter. Every claim now states the **git-checkable 28 minutes** (held-out list committed 08:24:14 →
  scorer first committed 08:52:32). Found while preparing this repository; the
  original figure was not verifiable by anyone reading `git log`.
- **The pre-registration has been appended to twice since it was hashed.** The
  file hashed `d3e24b77` is the version at commit `19684f2`, recoverable with
  `git show 19684f2:docs/MATRIX_PREREG.md`. Disclosed appends followed (5 commits touch the file) — a
  knockdown-count correction and a stale-count pointer — so the working copy now
  hashes `79269ce5`. **The original was never edited in place**; both additions sit
  below the original text, which remains visible and unchanged.

- **Two crashes during the held-out run** (undefined coherence at <2 members;
  BH correction on zero scoreable perturbations). Guarded with neutral
  training-mean imputation. **Three of ten rows had already printed** when the
  first guard was written, so the set was partially visible. The frozen predictor
  was not modified.
- **A denominator error** in an earlier build: `avg_rank` spans 11,258
  perturbation rows, not 9,837 unique targets, which produced percentages over
  100%. Found and corrected.
- **Two tier labels were wrong for K562** — MBTPS2 and LDLR cross the essentiality
  line in the cell line we actually scored, though the 1,178-line mean says
  otherwise. Annotated rather than silently re-tiered.
- **A statistic bug in our own freeze code** reported 5 distinct evidence sources
  instead of 34 (`value_counts().nunique()` counts frequencies, not values).
  Caught before commit.
- **A commit message gave the wrong cause for a number moving.** Commit
  `9d0c2f4` explains the assertion count going 357 → 358 as the tool-status
  guard "picking up benchflow being installed again". That is false. Checking
  out both commits and diffing the check names shows exactly one assertion
  appeared — `src/literature_audit.py parses` — because the suite runs a parse
  check per module in `src/`, and that file landed in the same commit. The count
  is **not** environment-dependent, and CI, which never installs benchflow,
  reports the same total as this machine. The message is left as pushed rather
  than rewritten, because teammates had already pulled it; this entry is the
  correction. Recorded because a wrong causal story about why a number changed
  is the same defect class as a wrong number, and this project has no standing
  to point that out in other people's work while leaving it in its own history.
- **The MCP server only worked from one directory, and that is the directory we
  always demonstrated it from.** `results/frozen/` was resolved against the
  caller's working directory, so the server started fine from the repo root and
  died with `FileNotFoundError` anywhere else — which is to say, in every real
  MCP client, since a client launches a server from its own cwd. Nobody had
  started it the way a stranger would. Both modules now anchor to their own file
  location, and the README carries a tested, copy-pasteable client config.
- **`--help` runs the pipeline.** With one exception the modules in `src/` do
  not parse arguments, so `python -m src.sweep --help` ignores the flag and
  spends fifteen minutes doing the sweep, and the `freeze_*` modules rewrite
  their outputs. Found by trying it. Nothing is damaged — every step is
  deterministic and the files land byte-identical, which is the reproducibility
  property doing its job — but a stranger asking for help should not trigger a
  write. Not fixed, and the reason is a real trade: `src/score_k562.py` is
  byte-frozen at sha256 `2abfdc6f…` and verified on load, so adding argument
  parsing to it would invalidate every number here. Documented in the README
  instead, under "Running things in `src/`".
- **A red commit was pushed.** `776d687` went out with four failing count checks,
  because the `make test` that should have gated it was chained behind a `grep`
  that succeeded on the failure output. Green again one commit later at
  `9d0c2f4`. An exit code was read from the wrong end of a pipe.

## 8. Not attempted

Sanger KY cross-library agreement (specified, never run) · scbench (no API key, no
Latch credentials — **we have no score and claim none**) · Benchling write-back
(blocked on account tier) · phenotypic validation of any kind. **Transcriptional
movement is not phenotypic reversal, and we make no therapeutic claim.**
