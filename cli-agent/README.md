# Galaxy CLI Agent

A natural language command-line interface for interacting with Galaxy bioinformatics platform.

## Overview

Galaxy CLI Agent provides both a structured command-line interface and an interactive natural language interface for working with Galaxy. It leverages Pydantic AI to create a smart agent that can interpret user requests, perform Galaxy operations, and present results in a user-friendly manner.

## Features

- **Natural Language Interface**: Use plain English to interact with Galaxy
- **Intelligent Query Processing**: Understands bioinformatics terms and workflows
- **Methods Generation**: Generate academic methods sections from Galaxy histories
- **Rich CLI Interface**: Beautiful command-line output with tables and panels
- **Comprehensive Commands**: Structured commands for tools, workflows, histories, and files
- **Interactive Mode**: Conversational interface for exploratory analysis

## Installation

### Quick Start

```bash
# Clone the repository (if not already done)
git clone https://github.com/galaxyproject/galaxy-mcp.git
cd galaxy-mcp

# Install all components from workspace root
make install-all

# Or install CLI agent specifically
cd cli-agent
uv sync --all-extras
```

### Requirements

- Python 3.10+
- uv (Python package manager)
- Galaxy MCP server (optional but recommended)

## Configuration

### 1. Galaxy Credentials (Required)

Set your Galaxy instance credentials:

```bash
# Option A: Environment variables
export GALAXY_URL="https://usegalaxy.org"
export GALAXY_API_KEY="your_galaxy_api_key_here"

# Option B: Create a .env file
cat > .env << EOF
GALAXY_URL=https://usegalaxy.org
GALAXY_API_KEY=your_galaxy_api_key_here
EOF
```

### 2. MCP Server Connection (Recommended)

The CLI agent works best with the Galaxy MCP server running:

```bash
# In terminal 1: Start the MCP server
cd mcp-server-galaxy-py
uv run fastmcp dev src/galaxy_mcp/server.py

# The server will run at http://localhost:3000/sse by default
```

The CLI agent will automatically connect to the MCP server if it's running.

### 3. Pydantic AI Configuration

The CLI agent uses Pydantic AI with Google's Gemini model. The model access is handled automatically by Pydantic AI - no separate API key needed.

## Usage

### Running the CLI Agent

From the workspace root:
```bash
# Using make
make run-cli

# Or directly with uv
uv run galaxy-agent --help
```

From the cli-agent directory:
```bash
uv run galaxy-agent --help
```

### Available Commands

```bash
galaxy-agent --help              # Show all commands
galaxy-agent connect             # Connect to Galaxy
galaxy-agent test-mcp            # Test MCP server connection
galaxy-agent interact            # Start interactive mode

# Subcommands
galaxy-agent tools --help        # Tool operations
galaxy-agent workflow --help     # Workflow operations  
galaxy-agent history --help      # History operations
galaxy-agent file --help         # File operations
galaxy-agent methods --help      # Methods generation
```

### Command Examples

#### 1. Test Connections

```bash
# Test MCP server connection
uv run galaxy-agent test-mcp

# Connect to Galaxy
uv run galaxy-agent connect
```

#### 2. Tool Operations

```bash
# Search for tools
uv run galaxy-agent tools search "fastq"
uv run galaxy-agent tools search "RNA-seq"

# Get tool details
uv run galaxy-agent tools details "bwa"
uv run galaxy-agent tools details "bwa" --io  # Include input/output details

# Get tool citations
uv run galaxy-agent tools citations "bwa"
```

#### 3. History Operations

```bash
# List all histories
uv run galaxy-agent history list

# Create a new history
uv run galaxy-agent history create "My RNA-seq Analysis"

# Get history details
uv run galaxy-agent history details "abc123def456"
```

#### 4. Workflow Operations

```bash
# Search for workflows
uv run galaxy-agent workflow search "rna-seq"
uv run galaxy-agent workflow search "variant calling"

# Import a workflow from IWC
uv run galaxy-agent workflow import "workflows/variant-calling/gatk4"
```

#### 5. File Operations

```bash
# Upload a file to current history
uv run galaxy-agent file upload /path/to/data.fastq

# Upload to specific history
uv run galaxy-agent file upload /path/to/data.fastq --history "abc123def456"
```

#### 6. Methods Generation

```bash
# Generate methods section from a history
uv run galaxy-agent methods generate "abc123def456"
```

### Interactive Mode (Natural Language)

The most powerful feature is the interactive mode:

```bash
uv run galaxy-agent interact
```

Example conversation:
```
Galaxy Agent> What tools are available for RNA-seq analysis?
[Agent searches and displays RNA-seq tools]

Galaxy Agent> Create a new history for my bacterial genome project
[Agent creates history "bacterial genome project"]

Galaxy Agent> Find workflows for variant calling
[Agent searches IWC for variant calling workflows]

Galaxy Agent> Show me tools that can work with VCF files
[Agent finds tools compatible with VCF format]

Galaxy Agent> Generate a methods section for history abc123
[Agent generates formatted methods with citations]

Galaxy Agent> help
[Shows available commands and examples]

Galaxy Agent> exit
```

### Tips for Natural Language Queries

The agent understands:
- **Tool searches**: "Find tools for alignment", "What can process FASTQ files?"
- **Workflow queries**: "Show workflows for RNA-seq", "Find single-cell analysis pipelines"
- **History management**: "Create a history called my_project", "List my histories"
- **Bioinformatics context**: "I need to analyze ChIP-seq data", "Tools for metagenomics"
- **File formats**: "Tools that work with BAM files", "VCF processing tools"

## Troubleshooting

### MCP Server Connection Issues

If you see warnings about MCP server connection:

1. **Check if MCP server is running**:
   ```bash
   curl http://localhost:3000/sse
   ```

2. **Verify the URL**:
   ```bash
   echo $MCP_SERVER_URL  # Should be http://localhost:3000/sse
   ```

3. **Start MCP server**:
   ```bash
   cd ../mcp-server-galaxy-py
   uv run fastmcp dev src/galaxy_mcp/server.py
   ```

### Galaxy Connection Issues

1. **Verify credentials**:
   ```bash
   echo $GALAXY_URL
   echo $GALAXY_API_KEY
   ```

2. **Test connection**:
   ```bash
   uv run galaxy-agent connect
   ```

3. **Check Galaxy instance**:
   - Ensure the Galaxy instance is running
   - Verify your API key is valid
   - Check network connectivity

### Common Error Messages

- **"Not connected to Galaxy"**: Run `galaxy-agent connect` first
- **"MCP server not available"**: Start the MCP server or check connection
- **"Method not found"**: Normal warning, agent will fall back to direct mode
- **"Failed to run tool"**: Check tool ID and required parameters

## Methods Generation

One of the most powerful features is automatic generation of academic methods sections:

```bash
uv run galaxy-agent methods generate <history_id>
```

This feature:
- Extracts all tools used in a history with parameters
- Collects proper citation information for each tool
- Generates a structured methods section ready for papers
- Formats citations in standard academic style

The generated output includes:
- Analysis overview
- Tool descriptions with versions
- Parameter settings used
- Properly formatted citations

## Architecture

The CLI agent is part of the Galaxy MCP workspace:

```
galaxy-mcp/
├── mcp-server-galaxy-py/    # Core Galaxy operations via MCP
├── cli-agent/               # Natural language CLI (this component)
└── pyproject.toml           # Workspace configuration
```

**Design principles**:
- CLI agent focuses on natural language understanding and UI
- MCP server handles all Galaxy API operations
- Clean separation ensures maintainability and reusability

## Development

### Using Make

The cli-agent directory includes a Makefile for common development tasks:

```bash
# Show all available targets
make help

# Install dependencies
make install      # Basic install
make dev          # Development install with all extras

# Testing
make test         # Run full test suite with coverage
make test-quick   # Run tests, stop on first failure
make test-watch   # Watch for changes and re-run tests

# Code quality
make lint         # Run linting and auto-fix issues
make format       # Format code only
make check        # Check code without modifications

# Running
make run          # Start the CLI agent
make run-help     # Show CLI help
make run-interact # Start interactive mode

# Cleanup
make clean        # Remove build artifacts
```

### Manual Commands

You can also run commands directly with uv:

```bash
# From cli-agent directory
uv run pytest
uv run pytest --cov=galaxy_cli_agent
uv run ruff check .
uv run mypy galaxy_cli_agent
uv run ruff format .
```

### From Workspace Root

When working from the Galaxy MCP workspace root:

```bash
# Run cli-agent tests
make test-cli

# Lint cli-agent code
make lint-cli

# Run the CLI agent
make run-cli
```

### Project Structure

```
cli-agent/
├── galaxy_cli_agent/
│   ├── agent.py    # Pydantic AI agent configuration
│   └── cli.py      # Typer CLI commands
├── tests/          # Test suite
├── pyproject.toml  # Package configuration
└── README.md       # This file
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes with tests
4. Run tests and linting
5. Submit a pull request

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Support

- Report issues: https://github.com/galaxyproject/galaxy-mcp/issues
- Galaxy help: https://help.galaxyproject.org/
- MCP documentation: https://modelcontextprotocol.io/
