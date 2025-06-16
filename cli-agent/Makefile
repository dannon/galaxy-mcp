# Galaxy CLI Agent Makefile

.PHONY: help install dev test lint format run clean

# Default target
help:
	@echo "Galaxy CLI Agent"
	@echo ""
	@echo "Available targets:"
	@echo "  install      - Install CLI agent dependencies"
	@echo "  dev          - Install in development mode with all extras"
	@echo "  test         - Run tests with coverage"
	@echo "  lint         - Run linting and formatting"
	@echo "  format       - Format code with ruff"
	@echo "  run          - Run the CLI agent"
	@echo "  clean        - Clean build artifacts"

# Installation
install:
	uv sync

dev:
	uv sync --all-extras

# Testing
test:
	uv run pytest --cov=galaxy_cli_agent --cov-report=html --cov-report=term-missing

test-watch:
	uv run pytest-watch

# Linting and formatting
lint:
	uv run ruff check . --fix
	uv run ruff format .

format:
	uv run ruff format .

check:
	uv run ruff check .
	uv run mypy galaxy_cli_agent

# Running
run:
	uv run galaxy-agent

run-help:
	uv run galaxy-agent --help

run-interact:
	uv run galaxy-agent interact

# Quick test commands
test-quick:
	uv run pytest -x

test-match:
	uv run pytest -k "$(MATCH)"

test-file:
	uv run pytest tests/$(FILE)

# Clean
clean:
	rm -rf build/ dist/ *.egg-info/ htmlcov/ .coverage
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# Pre-commit (run from workspace root)
pre-commit:
	cd .. && uv run pre-commit run --all-files --show-diff-on-failure
