# denali — reproduce every number on the page from a clean clone.
#
#   make judge-check   verify everything, no download, no keys, no network  (~30 s)
#   make setup     create the venv and install pinned deps
#   make data      print the ONE manual step (470 MB substrate download)
#   make all       reproduce everything deterministic   (~13 min, measured 12m05s)
#   make page      rebuild index.html from the frozen numbers
#   make clean     remove generated outputs (keeps data/raw)
#
# `make all` is deterministic: fixed seeds, checksummed inputs. It reproduces
# every figure and every number in results/frozen/ bit-for-bit.
#
# It does NOT re-run the two live-API steps (Europe PMC and Paperclip
# retrieval). Those indexes change, so their outputs are committed as dated
# observations. See `make retrieval` and docs/PRIOR_WORK.md.

# Overridable so CI can run the suite against the runner's interpreter:
#   make test PY=python
# It was hardcoded, which is why the CI badge was red from the day it was added.
PY ?= .venv/bin/python
RAW := data/raw

.PHONY: all setup data check test judge-check retrieval page clean

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
	@echo "== 1/10 score program A (UPR)                          ~11 s"
	$(PY) -m src.score_k562 HALLMARK_UNFOLDED_PROTEIN_RESPONSE results/discovery/k562_upr_reversal.csv
	@echo "== 2/10 program A: RPE1 arm, DepMap filter, 4 controls  ~4 min"
	$(PY) -m src.build2 HALLMARK_UNFOLDED_PROTEIN_RESPONSE results/discovery/k562_upr_reversal.csv results/discovery/upr
	@echo "== 3/10 score program B (held out)                      ~11 s"
	$(PY) -m src.score_k562 HALLMARK_CHOLESTEROL_HOMEOSTASIS results/discovery/k562_chol_reversal.csv
	@echo "== 4/10 program B: RPE1 arm, DepMap filter, 4 controls  ~4 min"
	$(PY) -m src.build2 HALLMARK_CHOLESTEROL_HOMEOSTASIS results/discovery/k562_chol_reversal.csv results/discovery/chol
	@echo "== 5/10 freeze programs A and B                         ~1 min"
	$(PY) -m src.freeze
	@echo "== 6/10 sweep all 50 Hallmark programs                  ~9 min"
	$(PY) -m src.sweep
	@echo "== 7/10 freeze the matrix, then the predictor           ~1 min"
	$(PY) -m src.freeze_matrix
	$(PY) -m src.freeze_predictor
	@echo "== 8/10 score the held-out ten against the frozen model ~3 min"
	$(PY) -m src.score_heldout
	@echo "== 9/10 figures + post-freeze sensitivity checks         ~1 min"
	$(PY) -m src.figures_matrix
	$(PY) -m src.sensitivity_stripped
	$(PY) -m src.vif_camera
	$(PY) -m src.engagement_bound
	@echo "== 10/10 second cell line, then cross-screen concordance     ~1 min"
	$(PY) -m src.rpe1_arm
	$(PY) -m src.concordance
	@echo "== freeze the three proposals the page renders          ~1 s"
	$(PY) -m src.freeze_proposals
	@echo "== build the page from the frozen numbers"
	$(PY) -m src.build_page
	@echo "== invariants: every number must match the committed frozen files"
	@$(MAKE) --no-print-directory test
	@echo ""
	@echo "DONE. Every number reproduced and every invariant held."
	@echo "     git diff --stat results/frozen/   # should be empty"

test:
	@$(PY) tests/test_frozen_invariants.py
	@$(PY) tests/test_cross_surface.py

judge-check:
	@echo "denali — judge check. No download, no API key, no network, no account."
	@echo "Everything below runs against files committed in this repository."
	@echo ""
	@echo "[1/4] invariants over the frozen interface"
	@$(PY) tests/test_frozen_invariants.py | tail -1
	@$(PY) tests/test_cross_surface.py | tail -1
	@echo ""
	@echo "[2/4] the packaged tool, and whether it still computes what the paper published"
	@$(PY) -m pytest packages/denali-audit/tests -q 2>/dev/null | tail -1 || \
		echo "  (pip install -e packages/denali-audit to run these)"
	@echo ""
	@echo "[3/4] the tool, on a g:Profiler-shaped export of our own screen"
	@PYTHONPATH=packages/denali-audit $(PY) -m denali_audit.cli audit \
		examples/example_gprofiler.csv | sed -n '1,6p'    
	@echo ""
	@echo "[4/4] the correction applied — what leaves the top ten"
	@PYTHONPATH=packages/denali-audit $(PY) -m denali_audit.cli rerank \
		examples/example_gprofiler.csv --top 10 | sed -n '3,13p'    
	@echo ""
	@echo "Done. Full reproduction from raw data needs the 470 MB substrate: make data && make all"

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
	rm -rf results/frozen results/figures/*.png results/sensitivity/*.json index.html
	@echo "removed generated outputs. data/raw kept."
