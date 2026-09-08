# Changelog

All notable changes to this project are documented here. Format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/); this project
tracks [Semantic Versioning](https://semver.org/), though as a research
tool pre-1.0, 0.x releases may still change the audit's numbers if a bug
in the maths is found. Seeded from `git log` (264 commits, 2026-08-15 to
2026-09-07); dates and one-line entries below are condensed from the
actual commit subjects rather than a 1:1 mirror of them.

## [0.1.0] - 2026-09-07

First tagged release. `packages/denali-audit` was already at
`version = 0.1.0` in its own metadata; this is the first git tag for the
repository as a whole.

### Added (this pass)
- `pyproject.toml` with a `[tool.ruff]` config, a `ruff` job in
  `.github/workflows/ci.yml`, and `.pre-commit-config.yaml` pinned to the
  same ruff version.
- Two tests in `packages/denali-audit/tests/test_core.py` pinning
  `rerank()`'s residuals/ranks/survivors and `audit()`'s
  `r2_size_alone` to values derived independently (textbook
  covariance/variance formula, not `np.polyfit`) on a small hand-chosen
  8-set dataset. Mutation-checked.
- A "Jump to" table of contents and a third quickstart command
  (`denali rerank ... --top 10`) in the README's top screen.
- This file.

### Fixed (this pass)
- `packages/denali-audit/tests/test_core.py` defined
  `test_refuses_too_few_sets()` twice (once for `audit()`, once for
  `baseline()`); Python kept only the second, so the first was never
  collected by pytest. Renamed both.
- A duplicate `"external_nulls"` key in
  `tests/test_frozen_invariants.py`'s `NON_ARM_DIRS`, which silently
  discarded the first entry's explanation.
- 32 real `ruff` findings (unused imports, extraneous f-string prefixes,
  multi-import lines) and 6 unused local variables, all mechanical.
- The README's top-screen terminal transcript and the Architecture
  diagram still showed the pre-2026-08-17 `CONFOUNDED:` verdict wording;
  the verdict vocabulary went null-relative on 2026-08-17 and this
  transcript was never updated. `docs/img/use-it.png` was re-shot for
  the same reason.

See the PR for this pass for full verification detail (test counts
before/after, mutation-check transcripts).

## Development history (pre-0.1.0)

Built in a concentrated, hackathon-style burst (158 commits on
2026-08-15, 57 on 2026-08-16, 38 on 2026-08-17), then two later
maintenance passes (2026-09-04, 2026-09-06) that repaired CI. Condensed
by day; see `git log` for the full, self-narrating commit history — most
individual commit subjects already read as changelog entries in their
own right (e.g. *"The page kept printing CONFOUNDED after the package
stopped believing it"*).

- **2026-08-15** — Built the primary result: scored 50 MSigDB Hallmark
  programs against K562 CRISPRi knockdowns, pre-registered and opened a
  held-out ten-program set, froze the interface at `results/frozen/`,
  and wrote the first README/REPORT/LIMITATIONS. Added
  `tests/test_frozen_invariants.py`, which "immediately caught two
  published errors." Built the static `index.html` page, the MCP
  server, an interactive program explorer, and the RPE1 second-cell-line
  and cross-screen-concordance arms. Numerous same-day corrections:
  stale test/file counts, a corrupted identifier from a blanket text
  replacement, a tracked symlink standing in for `data/raw`, mismatched
  evaluation numbering, and a demo script timed at 4:41 against a
  claimed 3:05.
- **2026-08-16** — Packaged the audit as `denali-audit` (`pip install`
  installable, no `scipy` dependency), added a cross-surface invariant
  suite checking that every rendered surface agrees with every other
  one, and a second, independent implementation of the headline result
  that had to agree with the first before either was trusted. Reworked
  the product framing from "a study" to "a tool a stranger can run" —
  README opens with the tool rather than the finding, the demo runs the
  audit instead of narrating a paper, and the rerank table's 35 hand
  typed cells became re-derived from the packaged CLI. Fixed a
  first-clean-install crash and a screenshot showing a stale CLI
  command.
- **2026-08-17** — The verdict vocabulary changed from fixed R² bands
  (`CONFOUNDED` / `PARTIALLY CONFOUNDED`) to null-relative comparisons
  (`MORE`/`LESS`/`INDISTINGUISHABLE FROM ITS OWN NULL`), under a sealed
  pre-registration, after finding that "arithmetic scored as
  confounding" under the old bands. Fixed a constant-hit-column division
  by a denormal that had been silently reported as an all-clear, added
  the atlas membership rule, added the corpus and external-screen
  audits (evaluations 8–11), and found and recorded several
  meta-failures in the check suite itself — guards that passed while
  testing nothing, three surfaces disagreeing on the suite's own size,
  and the MCP server's only automated test running in neither `make
  test` nor CI.
- **2026-09-04 / 2026-09-06** — CI had been red since 2026-08-17 because
  the invariants suite imported a module (`pyyaml`) nobody had added to
  `requirements.txt`; fixed, and CI hardened (least-privilege token,
  superseded-run cancellation, current action majors, Dependabot for
  workflow actions, a job that builds `denali-audit`, checks its
  metadata, installs the wheel and runs the CLI).
