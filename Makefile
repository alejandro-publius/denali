# denali — reproduce every number on the page from a clean clone.
#
#   make setup     create the venv and install pinned deps
#   make data      print the ONE manual step (470 MB substrate download)
#   make all       reproduce everything deterministic   (~22 min)
#   make page      rebuild index.html from the frozen numbers
#   make clean     remove generated outputs (keeps data/raw)
#
# `make all` is deterministic: fixed seeds, checksummed inputs. It reproduces
# every figure and every number in results/frozen/ bit-for-bit.
#
# It does NOT re-run the two live-API steps (Europe PMC and Paperclip
# retrieval). Those indexes change, so their outputs are committed as dated
# observations. See `make retrieval` and docs/PRIOR_WORK.md.

PY := .venv/bin/python
RAW := data/raw

.PHONY: all setup data check test retrieval page clean

setup:
	uv venv --python 3.12 .venv
	uv pip install --python $(PY) -r requirements.txt

data:
	@echo "MANUAL STEP — 470 MB, ~2 min. figshare 403s on HEAD but 206 on ranged GET."
	@echo ""
	@echo "  mkdir -p data/raw"
	@echo "  curl -sL -o data/raw/K562_gwps_normalized_bulk_01.h5ad https://ndownloader.figshare.com/files/35773217"
	@echo "  curl -sL -o data/raw/rpe1_normalized_bulk_01.h5ad       https://ndownloader.figshare.com/files/35775512"
	@echo "  curl -sL -o data/raw/CRISPRGeneEffect.csv               https://ndownloader.figshare.com/files/51064667"
	@echo "  curl -sL -o data/raw/Model.csv                          https://ndownloader.figshare.com/files/51065297"
	@echo ""
	@echo "Verify:  md5 data/raw/*.h5ad data/raw/*.csv"
	@echo "  K562_gwps_normalized_bulk_01.h5ad  a3dfaa94ea8724217f5ecb1e14a5f0c8"
	@echo "  rpe1_normalized_bulk_01.h5ad       6f1e7d6a09e2f869759e3c4526b7f171"
	@echo "  CRISPRGeneEffect.csv               6edf7ade09b9b34199210b559d4745d3"
	@echo "  Model.csv                          675210d17675f3517b0ce39a3c274f16"

check:
	@test -f $(RAW)/K562_gwps_normalized_bulk_01.h5ad || (echo "MISSING substrate. Run: make data" && exit 1)
	@test -f $(RAW)/rpe1_normalized_bulk_01.h5ad      || (echo "MISSING substrate. Run: make data" && exit 1)
	@test -f $(RAW)/CRISPRGeneEffect.csv              || (echo "MISSING DepMap. Run: make data" && exit 1)
	@test -f $(RAW)/Model.csv                         || (echo "MISSING DepMap. Run: make data" && exit 1)
	@echo "substrate present"

all: check
	@echo "== 1/9  score program A (UPR)                          ~11 s"
	$(PY) -m src.score_k562 HALLMARK_UNFOLDED_PROTEIN_RESPONSE results/discovery/k562_upr_reversal.csv
	@echo "== 2/9  program A: RPE1 arm, DepMap filter, 4 controls  ~4 min"
	$(PY) -m src.build2 HALLMARK_UNFOLDED_PROTEIN_RESPONSE results/discovery/k562_upr_reversal.csv results/discovery/upr
	@echo "== 3/9  score program B (held out)                      ~11 s"
	$(PY) -m src.score_k562 HALLMARK_CHOLESTEROL_HOMEOSTASIS results/discovery/k562_chol_reversal.csv
	@echo "== 4/9  program B: RPE1 arm, DepMap filter, 4 controls  ~4 min"
	$(PY) -m src.build2 HALLMARK_CHOLESTEROL_HOMEOSTASIS results/discovery/k562_chol_reversal.csv results/discovery/chol
	@echo "== 5/9  freeze A/B + divergence                         ~1 min"
	$(PY) -m src.freeze
	$(PY) -m src.divergence_repair
	@echo "== 6/9  sweep all 50 Hallmark programs                  ~9 min"
	$(PY) -m src.sweep
	@echo "== 7/9  freeze the matrix, then the predictor           ~1 min"
	$(PY) -m src.freeze_matrix
	$(PY) -m src.freeze_predictor
	@echo "== 8/9  score the held-out ten against the frozen model ~3 min"
	$(PY) -m src.score_heldout
	@echo "== 9/9  figures + post-freeze sensitivity check          ~1 min"
	$(PY) -m src.figures_matrix
	$(PY) -m src.sensitivity_stripped
	@echo "== build the page from the frozen numbers"
	$(PY) -m src.build_page
	@echo "== invariants: every number must match the committed frozen files"
	@$(MAKE) --no-print-directory test
	@echo ""
	@echo "DONE. Every number reproduced and every invariant held."
	@echo "     git diff --stat results/frozen/   # should be empty"

test:
	@$(PY) tests/test_frozen_invariants.py

retrieval:
	@echo "LIVE API — will NOT reproduce the committed numbers. The indexes change."
	@echo "Committed outputs are dated observations; see docs/PRIOR_WORK.md."
	@echo "Requires: paperclip login"
	$(PY) src/probe_retrieval.py
	$(PY) -m src.build_program
	$(PY) -m src.paperclip_program

page:
	$(PY) -m src.build_page
	@echo "open index.html"

clean:
	rm -rf results/frozen results/figures/*.png results/sensitivity/stripped_model.json index.html
	@echo "removed generated outputs. data/raw kept."
