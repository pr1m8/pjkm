SHELL := /bin/bash
.DEFAULT_GOAL := help

.PHONY: help install test lint fmt typecheck check cov clean

install: ## Install dev dependencies
	pdm install -G dev

test: ## Run tests
	pdm run pytest

lint: ## Run linters
	pdm run ruff check src tests

fmt: ## Format code
	pdm run ruff format src tests

typecheck: ## Run type checker
	pdm run pyright src

check: fmt lint test ## Run all checks

cov: ## Run tests with coverage
	pdm run pytest --cov --cov-report=html --cov-report=term-missing

clean: ## Remove build artifacts
	rm -rf dist/ build/ *.egg-info .pytest_cache .mypy_cache .ruff_cache htmlcov/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'
