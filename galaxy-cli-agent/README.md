# Galaxy CLI Agent

A command-line interface for interacting with Galaxy using Pydantic AI.

## Overview

Galaxy CLI Agent provides both a structured command-line interface and an interactive natural language interface for working with Galaxy. It leverages Pydantic AI to create a smart agent that can interpret user requests, perform Galaxy operations, and present results in a user-friendly manner.

## Features

- **Galaxy Connection**: Connect to any Galaxy instance with a URL and API key
- **Tools Management**: Search, view details, and execute Galaxy tools
- **Workflow Integration**: Search workflows in IWC and import them to Galaxy
- **History Operations**: Manage Galaxy histories and datasets
- **Interactive Mode**: Use natural language to interact with Galaxy

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/galaxy-cli-agent.git
cd galaxy-cli-agent

# Install the package
pip install -e .
```

## Usage

### Setting Galaxy Connection

You can set Galaxy credentials in several ways:

1. Using environment variables:
```bash
export GALAXY_URL=<galaxy_url>
export GALAXY_API_KEY=<galaxy_api_key>
```

2. Using a `.env` file in your current directory:
```
GALAXY_URL=<galaxy_url>
GALAXY_API_KEY=<galaxy_api_key>
```

3. Providing them as command-line arguments:
```bash
galaxy-agent connect --url <galaxy_url> --api-key <galaxy_api_key>
```

### Command Line Examples

Search for tools:
```bash
galaxy-agent tools search fastq
```

Get tool details:
```bash
galaxy-agent tools details <tool_id> --io
```

List all histories:
```bash
galaxy-agent history list
```

Create a new history:
```bash
galaxy-agent history create "My Analysis"
```

Search for workflows in IWC:
```bash
galaxy-agent workflow search rna-seq
```

Import a workflow from IWC:
```bash
galaxy-agent workflow import <trs_id>
```

### Interactive Mode

Start the interactive mode for natural language interaction:
```bash
galaxy-agent interact
```

Example interactions:
```
Galaxy Agent> Show me tools for RNA-seq analysis
Galaxy Agent> Create a new history called RNA-seq analysis
Galaxy Agent> Find workflows for single-cell RNA-seq
```

## Development

### Requirements

- Python 3.9+
- Pydantic 2.0+
- Pydantic AI
- httpx
- typer
- rich

### Development Setup

Install development dependencies:
```bash
pip install -e ".[dev]"
```

Run tests:
```bash
pytest
```

## License

MIT