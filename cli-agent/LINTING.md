# CLI Agent Linting Setup

## Comparison with MCP Server

### Common Setup
Both cli-agent and mcp-server-galaxy-py now use:
- **ruff** for linting and formatting (v0.11.13 in mcp-server, latest in cli-agent)
- Same ruff configuration:
  - Line length: 100
  - Indent width: 4
  - Target version: Python 3.10
  - Selected rules: E, F, W, I, N, B, UP, A, C4, SIM, PT
  - Ignored rules: F403, B904, B017, PT011, SIM117

### Differences
1. **Pre-commit**:
   - Both projects share a single .pre-commit-config.yaml at the workspace root
   - This ensures consistent formatting rules across the entire codebase

2. **Black**:
   - cli-agent includes black in dev dependencies (for compatibility)
   - mcp-server relies only on ruff for formatting

3. **Type checking**:
   - Both have mypy configured
   - cli-agent includes it in dev dependencies

## Running Linting

From workspace root:
```bash
# Lint both projects
make lint

# Lint CLI agent only
make lint-cli

# Lint MCP server only
make lint-mcp
```

From cli-agent directory:
```bash
# Check and auto-fix issues
uv run ruff check . --fix

# Format code
uv run ruff format .

# Type checking
uv run mypy galaxy_cli_agent
```

## Fixed Issues
- Updated type annotations from `Optional[X]` to `X | None` (PEP 604 style)
- Fixed long lines by splitting strings and expressions
- Removed trailing whitespace
- Applied consistent formatting with ruff

## Pre-commit Setup
Pre-commit hooks are managed at the workspace root. To enable them:
```bash
# From workspace root
uv run pre-commit install
```

This will run ruff checks automatically before each commit for all projects in the workspace.
