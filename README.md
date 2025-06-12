# Galaxy MCP Workspace

This project provides comprehensive tooling for interacting with the Galaxy bioinformatics platform using AI assistants and natural language interfaces. It includes both a Model Context Protocol (MCP) server and an intelligent CLI agent powered by Pydantic AI.

## Project Overview

This repository contains two main components:

1. **Galaxy MCP Server** (`mcp-server-galaxy-py/`) - A Python MCP server that provides direct Galaxy API access
2. **Galaxy CLI Agent** (`cli-agent/`) - An intelligent CLI that uses natural language to interact with Galaxy via the MCP server

The MCP server provides the core Galaxy operations, while the CLI agent adds natural language understanding and user-friendly interfaces.

## Key Features

### MCP Server Features
- **Galaxy Connection**: Connect to any Galaxy instance with a URL and API key
- **Server Information**: Retrieve comprehensive server details including version, configuration, and capabilities
- **Tools Management**: Search, view details, and execute Galaxy tools
- **Workflow Integration**: Access and import workflows from the Interactive Workflow Composer (IWC)
- **History Operations**: Manage Galaxy histories and datasets
- **File Management**: Upload files to Galaxy from local storage
- **Tool Citations**: Get citation information for proper academic attribution

### CLI Agent Features
- **Natural Language Interface**: Use plain English to interact with Galaxy
- **Intelligent Query Processing**: Understands bioinformatics terms and workflows
- **Methods Generation**: Automatically generate academic methods sections from Galaxy histories
- **Rich CLI Interface**: Beautiful command-line output with tables and panels
- **Comprehensive Commands**: Structured commands for tools, workflows, histories, and files
- **Interactive Mode**: Conversational interface for exploratory analysis

## Quick Start

### CLI Agent (Recommended for most users)

The CLI agent provides an intuitive interface for Galaxy operations:

```bash
# Install the workspace with CLI agent
git clone https://github.com/galaxyproject/galaxy-mcp.git
cd galaxy-mcp
make install-all

# Set up environment variables
export GALAXY_URL=<your_galaxy_url>
export GALAXY_API_KEY=<your_galaxy_api_key>

# Run the CLI agent
uv run galaxy-agent --help

# Interactive mode for natural language queries
uv run galaxy-agent interact
```

### MCP Server (For AI assistant integration)

For direct MCP server usage with AI assistants:

```bash
# Run the server directly without installation
uvx galaxy-mcp

# Run with MCP developer tools for interactive exploration
uvx --from galaxy-mcp mcp dev galaxy_mcp.server

# Run as a deployed MCP server
uvx --from galaxy-mcp mcp run galaxy_mcp.server
```

### Environment Setup

Set up your Galaxy credentials via environment variables:

```bash
export GALAXY_URL=<galaxy_url>
export GALAXY_API_KEY=<galaxy_api_key>
```

Or create a `.env` file in your working directory:
```
GALAXY_URL=<galaxy_url>
GALAXY_API_KEY=<galaxy_api_key>
```

## CLI Agent Examples

### Structured Commands

```bash
# Search for tools
uv run galaxy-agent tools search "RNA-seq"

# Get tool details
uv run galaxy-agent tools details "bwa" --io

# List histories
uv run galaxy-agent history list

# Create a new history
uv run galaxy-agent history create "My Analysis"

# Search workflows
uv run galaxy-agent workflow search "variant calling"

# Generate methods section from a history
uv run galaxy-agent methods generate "abc123def456"
```

### Natural Language Interface

```bash
# Start interactive mode
uv run galaxy-agent interact

# Example interactions:
Galaxy Agent> Find tools for RNA-seq analysis
Galaxy Agent> Create a new history called "Bacterial Genome Analysis"
Galaxy Agent> Show me workflows for single-cell RNA-seq
Galaxy Agent> What tools can process VCF files?
Galaxy Agent> Generate a methods section for my history abc123
```

### Alternative Installation

```bash
# Install from PyPI
pip install galaxy-mcp

# Or from source
cd mcp-server-galaxy-py
pip install -r requirements.txt
mcp run main.py
```

## Architecture

This workspace uses a clean separation of concerns:

```
galaxy-mcp/
├── mcp-server-galaxy-py/     # Core Galaxy MCP server
│   ├── src/galaxy_mcp/       # Galaxy API operations
│   └── tests/                # MCP server tests
├── cli-agent/                # Natural language CLI
│   ├── galaxy_cli_agent/     # CLI and agent code
│   └── tests/                # CLI agent tests
├── pyproject.toml            # Workspace configuration
└── Makefile                  # Build and test automation
```

### Component Responsibilities

**MCP Server** (`mcp-server-galaxy-py/`):
- Direct Galaxy API integration via BioBlend
- Core operations: connect, search tools, run tools, manage histories
- Workflow operations: search IWC, import workflows
- File operations: upload, manage datasets
- Job monitoring and tool citations

**CLI Agent** (`cli-agent/`):
- Natural language query interpretation
- User-friendly command-line interface
- Methods section generation for academic papers
- Rich output formatting and interactive modes
- Uses MCP server for all Galaxy operations

### Data Flow

1. User issues natural language query to CLI agent
2. CLI agent interprets query using Pydantic AI
3. CLI agent calls appropriate MCP server tools
4. MCP server executes Galaxy API operations
5. Results flow back through CLI agent for formatting
6. User sees rich, formatted output

This architecture ensures:
- **Single source of truth** for Galaxy operations (MCP server)
- **Reusable components** (MCP server can be used by other clients)
- **Clean separation** of Galaxy API logic from UI logic
- **Easy testing** (each component can be tested independently)

## Development

### Workspace Setup

```bash
# Clone and set up the workspace
git clone https://github.com/galaxyproject/galaxy-mcp.git
cd galaxy-mcp

# Install all components
make install-all

# Or install specific components
make install-mcp    # MCP server only
make install-cli    # CLI agent only
```

### Development Commands

```bash
# Run tests for all components
make test

# Run tests for specific components
make test-mcp
make test-cli

# Run linting
make lint

# Run MCP server in development mode
make run-mcp

# Run CLI agent
make run-cli
```

### Component-Specific Development

- **MCP Server**: See [mcp-server-galaxy-py/README.md](mcp-server-galaxy-py/README.md)
- **CLI Agent**: See [cli-agent/README.md](cli-agent/README.md)

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes with tests
4. Run `make test` and `make lint`
5. Submit a pull request

## License

[MIT](LICENSE)
