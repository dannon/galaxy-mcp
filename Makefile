# Galaxy MCP Workspace Makefile
# Manages both MCP server and CLI agent components

.PHONY: help install install-mcp install-cli install-all dev clean test test-mcp test-cli lint lint-mcp lint-cli build

# Default target
help:
	@echo "Galaxy MCP Workspace"
	@echo ""
	@echo "Available targets:"
	@echo "  install      - Install core workspace dependencies"
	@echo "  install-mcp  - Install MCP server dependencies"
	@echo "  install-cli  - Install CLI agent dependencies"
	@echo "  install-all  - Install all dependencies (MCP + CLI + dev)"
	@echo "  dev          - Install in development mode with all features"
	@echo ""
	@echo "  test         - Run all tests (MCP + CLI)"
	@echo "  test-mcp     - Run MCP server tests only"
	@echo "  test-cli     - Run CLI agent tests only"
	@echo ""
	@echo "  lint         - Run linting for all components"
	@echo "  lint-mcp     - Run linting for MCP server only"
	@echo "  lint-cli     - Run linting for CLI agent only"
	@echo ""
	@echo "  run-mcp      - Run MCP server in development mode"
	@echo "  run-cli      - Run CLI agent"
	@echo ""
	@echo "  build        - Build distribution packages"
	@echo "  clean        - Clean build artifacts"
	@echo ""
	@echo "For component-specific targets, see:"
	@echo "  make -C mcp-server-galaxy-py help"
	@echo "  make -C cli-agent help"

# Installation targets
install:
	uv sync

install-mcp:
	uv sync --extra mcp-server

install-cli:
	uv sync --extra cli

install-all:
	uv sync --all-extras

dev: install-all
	uv run pre-commit install

# Test targets
test: test-mcp test-cli

test-mcp:
	cd mcp-server-galaxy-py && uv run pytest --cov=galaxy_mcp --cov-report=html --cov-report=term-missing

test-cli:
	$(MAKE) -C cli-agent test

# Lint targets
lint: lint-mcp lint-cli

lint-mcp:
	cd mcp-server-galaxy-py && uv run pre-commit run --all-files --show-diff-on-failure

lint-cli:
	$(MAKE) -C cli-agent lint

# Run targets
run-mcp:
	cd mcp-server-galaxy-py && uv run fastmcp dev src/galaxy_mcp/server.py

run-cli:
	$(MAKE) -C cli-agent run

# Build targets
build:
	cd mcp-server-galaxy-py && uv build
	cd cli-agent && uv build

clean:
	rm -rf build/ dist/ *.egg-info/
	cd mcp-server-galaxy-py && rm -rf build/ dist/ *.egg-info/ htmlcov/
	cd cli-agent && rm -rf build/ dist/ *.egg-info/ htmlcov/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# Quick development helpers
quick-test-mcp:
	cd mcp-server-galaxy-py && uv run pytest -x

quick-test-cli:
	$(MAKE) -C cli-agent test-quick
