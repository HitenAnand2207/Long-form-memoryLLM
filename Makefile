# Long-Form Memory System — Makefile
# Usage: make <target>
# Requires Python 3.9+ in PATH or an activated virtual environment.

PYTHON  ?= python
PIP     ?= pip
VENV    := .venv
SRC     := src

.PHONY: help install install-full demo api test eval clean benchmark-relevance

help:            ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*##' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*## "}; {printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}'

# ── Setup ──────────────────────────────────────────────────────────────────────

install:         ## Install minimal deps (no FAISS/torch — fast)
	$(PIP) install -r requirements-minimal.txt

install-full:    ## Install all deps including FAISS + sentence-transformers
	$(PIP) install -r requirements.txt
	$(PIP) install faiss-cpu sentence-transformers

# ── Run ────────────────────────────────────────────────────────────────────────

run: demo        ## Alias → runs the scripted Turn-1-to-937 demo

demo:            ## Scripted pipeline demo (Turn 1 → 937 long-range recall)
	$(PYTHON) -m src.run_demo

api:             ## Start Flask REST API server on http://localhost:5000
	$(PYTHON) -m src.api_server

interactive:     ## Launch interactive terminal chat with memory
	$(PYTHON) -m src.demo

benchmark:       ## Run 1,000-turn performance benchmark
	$(PYTHON) -c "import sys; sys.argv=['demo','3']; exec(open('src/demo.py').read())"

benchmark-relevance: ## Compare retrieval relevance before/after token normalization
	$(PYTHON) -m pytest -q tests/test_retrieval_benchmark.py

# ── Quality ────────────────────────────────────────────────────────────────────

test:            ## Run pytest regression suite
	$(PYTHON) -m pytest tests/ -v

eval:            ## Full evaluation suite → evaluation_report.json
	$(PYTHON) $(SRC)/evaluate.py

diagnose:        ## Check environment and report missing packages
	$(PYTHON) diagnose.py

# ── Housekeeping ───────────────────────────────────────────────────────────────

clean:           ## Remove generated data, caches, and build artefacts
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	rm -f data/memories.db data/demo_memories.db evaluation_report.json
	@echo "Clean done."
