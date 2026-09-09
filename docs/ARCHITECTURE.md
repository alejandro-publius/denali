# Architecture

```mermaid
flowchart TB
  subgraph sub[" "]
    direction TB
    PC["Paperclip / GXL<br/>113 gene queries"] --> CIT["citations + blind probe"]
    CIT --> AUD["retrieval audit<br/>34 sources · 19 of 20 · FIG 4"]
  end

  REP["Replogle K562 Perturb-seq<br/>11,258 × 8,248 · CC BY 4.0"] --> SC
  GMT["MSigDB Hallmark<br/>50 programs"] --> SC
  SC["src/score_k562.py 🔒<br/>byte-frozen scorer · sha256 2abfdc6f…<br/>every arm asserts this hash before it runs"] --> SW
  SW["src/sweep.py<br/>rank-based reversal, 50 × 9,837"] --> MAT

  DEP["DepMap 24Q4 Chronos<br/>1,178 lines · CC BY 4.0"] --> FM
  MAT["matrix.csv"] --> FM["src/freeze_matrix.py"]
  FM --> FROZEN

  FROZEN["results/frozen/ 🔒<br/>matrix · program_summary<br/>provenance · proposals"] --> PRED
  PRED["src/freeze_predictor.py<br/>OLS on 6 features → predictor.json 🔒"] --> FREEZE

  FREEZE{{"FREEZE BOUNDARY<br/>predictor hashed"}} --> HO
  HO["src/score_heldout.py<br/>10 Reactome programs, opened after the freeze"] --> FROZEN

  FROZEN --> NEXT["src/next_experiment.py<br/>proposal + what would change my mind<br/>no branch tests a program name"]
  NEXT --> FZP["src/freeze_proposals.py<br/>the only writer of proposals.json"]
  FZP -->|"a test asserts the committed<br/>file still matches this"| FROZEN

  FROZEN --> PAGE["src/build_page.py → index.html<br/>+ the agent loop, in-browser"]
  FROZEN --> APP["app.py → Streamlit<br/>renders proposals.json"]
  FROZEN --> MCP["src/mcp_server.py → 6 tools<br/>2 read our result, 4 run the tool on yours"]
  FROZEN --> VIF["src/vif_camera.py<br/>post-freeze: VIF = 1+(m−1)ρ̄"]
  FROZEN --> BENCH["benchmarks/denali-gate-trap<br/>our finding, as a task for other agents"]
  FROZEN --> AUD2["src/audit_screen.py<br/>the same check, on anyone's screen"]
  AUD2 --> PKG["packages/denali-audit 📦<br/>pip installable · core.py vendored verbatim"]
  PKG --> DA["denali audit<br/>10 formats auto-detected · verdict + percentile"]
  DA --> DR["denali rerank<br/>applies the correction · 3 of our top 10 hold"]
  PKG --> WASM["audit.html 🌐<br/>the package itself in WebAssembly<br/>your file, your browser, nothing uploaded"]
  PKG -.->|"anti-drift test: audit() on the frozen<br/>data must return 0.4649 or CI fails"| FROZEN
  WASM -.->|"page-parity test: the inlined source must<br/>reproduce 0.4649, above its null, or CI fails"| PKG

  PKG --> BREADTH["results/breadth/<br/>3 domains that are not gene sets<br/>regions · metabolites · microbiome"]
  BREADTH --> NULL["null_baselines.py<br/>the no-biology value per mapping"]
  NULL -.->|"BOUNDARY CONDITION, pointing back at the tool:<br/>where hits are counted over the set's own members,<br/>a large R² is arithmetic. None of the three cleared<br/>its own null. Ours does — 0.4649 vs 0.0182"| DA

  ORCS["BioGRID ORCS 2.0.18<br/>1,952 human screens · 418 publications"] --> CORP
  CORP["src/corpus_audit.py<br/>eval 10 · 1,272 screens meet the rule"] --> CRES
  CRES["results/corpus/<br/>median 0.224 · ours above the 90th pct"] --> REF
  REF["denali_audit/reference.py<br/>the corpus, embedded → percentile"] --> DA
  CRES --> CRR["src/corpus_rerank.py<br/>post-hoc · imports the shipped rerank()"]
  PKG -.->|"the same correction, run on<br/>the literature rather than on us"| CRR
  CRR --> CRRES["results/corpus_rerank/<br/>median screen keeps 9 of 10; we keep 3"]

  REP --> IND["src/independent_recompute.py<br/>reimplemented from the method section,<br/>never from the code"]
  IND -.->|"scipy · statsmodels at every step<br/>agrees to 0.000049 · asserted by the suite"| FROZEN
  FROZEN --> RP["src/rpe1_arm.py 🔒<br/>eval 5 · 2nd cell line, pre-registered"]
  RP --> CONC["src/concordance.py<br/>eval 6 · 26% of 'it replicated' is set size"]
  FROZEN --> CONC

  SC --> ANN["src/annotation_arm.py 🔒<br/>eval 7 · 793 sets, 4 collections, Modal"]
  GO["WikiPathways · Reactome · GO-BP<br/>10,352 sets"] --> ANN
  ANN --> ARES["results/annotation/<br/>UNDERPOWERED on 3 of 4"]

  EXT["CHANGE-seq · CRISPRme<br/>two published datasets, neither ours"] --> OT
  OT["src/offtarget_audit.py<br/>eval 8 · post-hoc, thresholds swept"] --> ORES["results/offtarget/"]

  MOD["src/modal_sweep.py<br/>50 programs / 10 containers"] -.->|"reproduces, does not produce"| FROZEN
  CRR --> MCR["src/modal_corpus_rerank.py<br/>1,272 screens fanned across containers"]
  MCR -.->|"same screen_row(), run distributed<br/>join + own-screen + agreement gates"| CRRES
  VIF -.->|"external theory<br/>Wu &amp; Smyth 2012"| CAM(["CAMERA"])
  AUD -.->|"audit only — never feeds the matrix"| PAGE

  style FROZEN fill:#f2f2f0,stroke:#1a4d7a,stroke-width:2px
  style FREEZE fill:#fff,stroke:#1a4d7a,stroke-width:2px,stroke-dasharray:4 3
  style sub fill:#fff,stroke:#e3e3e3,stroke-dasharray:3 3
  style MOD fill:#fff,stroke:#8c8c89,stroke-dasharray:4 3
  style CAM fill:#f2f2f0,stroke:#1a4d7a
  style SC fill:#fff,stroke:#1a4d7a,stroke-width:2px
  style FZP fill:#fff,stroke:#1a4d7a,stroke-width:2px
  style RP fill:#fff,stroke:#1a4d7a,stroke-width:2px
  style ANN fill:#fff,stroke:#1a4d7a,stroke-width:2px
  style ARES fill:#f7f7f8,stroke:#8c8c89
  style ORES fill:#f7f7f8,stroke:#8c8c89
  style PKG fill:#eef4ea,stroke:#3d6b2e,stroke-width:2px
  style DA fill:#eef4ea,stroke:#3d6b2e,stroke-width:2px
  style DR fill:#eef4ea,stroke:#3d6b2e,stroke-width:2px
  style REF fill:#f7f7f8,stroke:#8c8c89
  style CORP fill:#fff,stroke:#1a4d7a,stroke-width:2px
  style CRES fill:#f7f7f8,stroke:#8c8c89
  style CRR fill:#fff,stroke:#1a4d7a,stroke-width:2px
  style CRRES fill:#f7f7f8,stroke:#8c8c89
  style MCR fill:#fff,stroke:#8c8c89,stroke-dasharray:4 3
  style IND fill:#fff,stroke:#1a4d7a,stroke-width:2px
```

**The freeze boundary is the load-bearing part.** `results/frozen/` is written once per run and read by everything downstream; nothing after it recomputes. The predictor is fit on the 50 scored programs, serialised, and **hashed** — and only then are the ten held-out programs scored, with `src/score_heldout.py` verifying the hash at load and aborting on mismatch. Scoring them before the freeze would have let the model see its own test set; scoring them after means the failure it produced is a real failure.

**Evaluations 5–8 point sideways, and that is the whole discipline.** `src/annotation_arm.py`, `src/concordance.py`, `src/rpe1_arm.py` and `src/offtarget_audit.py` each write their own directory — `results/annotation/`, `results/concordance/`, `results/rpe1/`, `results/offtarget/` — and **not one of them has an edge back into `results/frozen/`.** That is deliberate. Every one of those arms was built after the primary was frozen, so any of them could have been used to quietly improve the headline: re-score with a looser gate, fold the second cell line in, let a 793-set sweep redefine the comparator. Pointing them sideways makes that impossible to do by accident rather than merely against the rules. What they are allowed to change is the *scope* of the claim — evaluation 7 narrowed it by showing more than half of GO Biological Process cannot be evaluated against this screen at all, and evaluation 8 widened it by finding the same confound in two clinical off-target datasets that have nothing to do with gene sets. Neither moved a number inside the freeze. The two arms that read the byte-frozen scorer, `src/annotation_arm.py` and `src/rpe1_arm.py`, assert its sha256 before they run and abort rather than proceed against a modified scorer.

**`src/freeze_proposals.py` is drawn as the only writer of `proposals.json` because that turned out to matter.** The three generated proposals the page renders are produced by `src/next_experiment.py` and serialised once by that script. It went stale — the generator gained a falsification field and the artifact was never rewritten — and because nothing checked the artifact against its generator, `make all` on a clean clone silently rewrote it and made the byte-identical reproduction claim false while every other test stayed green. The edge back into `results/frozen/` now carries that check.

**The dashed edges are claims you can check, and there are now four of them.** Modal points *into* `results/frozen/` rather than out of it: `src/modal_sweep.py` re-runs the sweep across ten containers and reproduces all 50 programs identically, so it verifies the frozen result without being allowed to produce it — it is deliberately not a `make all` step, and a test asserts that. The VIF edge points *outward*, to a statistical result published in 2012: our two dominant features turn out to be the two terms of CAMERA's variance-inflation factor, which we recovered from data rather than fitted to.

**The packaged tool is drawn downstream of the freeze, with one edge pointing back.** `packages/denali-audit` is what a stranger installs, and it is not a rewrite: `core.py` is the study's own maths vendored verbatim, `reference.py` carries the 1,272-screen corpus so an audit can say where a ranking sits rather than only what its R² is, and `denali rerank` applies the correction. The dashed edge back into `results/frozen/` is the claim that makes the whole arrangement honest — **a test runs the packaged `audit()` against the frozen research data and requires exactly `0.4649`**, the published headline. If the tool and the paper ever disagree, CI fails rather than the two quietly diverging and the README continuing to cite a number the shipped code no longer produces. That is the difference between a tool that came out of a study and a tool that merely resembles one.

**The two strongest validation artifacts are now drawn, because leaving them out flattered the diagram.** The first is the corpus: `src/corpus_audit.py` reads BioGRID ORCS 2.0.18, keeps the 1,272 screens that meet a stated inclusion rule, and writes `results/corpus/` — and the edge that matters runs from there into `denali_audit/reference.py`, because that is where the percentile a stranger sees comes from. Without that edge the tool appears to assert "worse than nine in ten screens" out of nowhere; with it, the claim has a substrate, an inclusion rule and a file. `src/corpus_rerank.py` then takes the *shipped* `rerank()` — imported from the package, not reimplemented — and runs it over the same 1,272 screens, which is why its edge comes from `packages/denali-audit` rather than from the study. The second is `src/independent_recompute.py`, which rebuilt the headline from this README's method section without reading the frozen code, and whose dashed edge into `results/frozen/` is an agreement to 0.000049 that the suite asserts. Both are checks *on* the project rather than steps *in* it, which is exactly why they were the easiest two to forget to draw.

**Paperclip is drawn as a side branch that terminates in the retrieval audit, because that is what it is.** It produced per-gene citations and a blind probe, and those numbers appear on the page — but nothing it generated feeds `matrix.csv`, the predictor, or any frozen result. The per-gene divergence table that once consumed it was withdrawn when guide-pair concordance made per-gene verdicts indefensible.
