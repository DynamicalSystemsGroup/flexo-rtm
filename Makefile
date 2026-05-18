# SPDX-License-Identifier: Apache-2.0
.PHONY: help sync test lint format parsimony all clean

help:
	@echo "Targets:"
	@echo "  sync       - uv sync (install env + dev deps)"
	@echo "  test       - uv run pytest -q"
	@echo "  lint       - uv run ruff check + uv run mypy"
	@echo "  format     - uv run ruff format"
	@echo "  parsimony  - build ontology/rtm.ttl and report triple count"
	@echo "  all        - parsimony + lint + test"
	@echo "  clean      - remove caches and build outputs"

sync:
	uv sync

test:
	uv run pytest -q

lint:
	uv run ruff check .
	uv run mypy

format:
	uv run ruff format .

parsimony:
	uv run python ontology/parsimony/build.py

all: parsimony lint test

clean:
	rm -rf .pytest_cache .mypy_cache .ruff_cache .hypothesis __pycache__ build dist *.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} +
