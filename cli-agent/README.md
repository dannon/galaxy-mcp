# Galaxy CLI Agent

A command-line interface for interacting with Galaxy using Pydantic AI.

## Overview

Galaxy CLI Agent provides both a structured command-line interface and an interactive natural language interface for working with Galaxy. It leverages Pydantic AI to create a smart agent that can interpret user requests, perform Galaxy operations, and present results in a user-friendly manner.

## Features

- **Galaxy Connection**: Connect to any Galaxy instance with a URL and API key
- **Tools Management**: Search, view details, and execute Galaxy tools
- **Workflow Integration**: Search workflows in IWC and import them to Galaxy
- **History Operations**: Manage Galaxy histories and datasets
- **File Upload**: Upload local files to Galaxy histories
- **Methods Generation**: Generate academic methods sections with citations from Galaxy histories
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

### Setting Up Google API Key for Gemini

The CLI agent uses Google's Gemini model for natural language understanding and generation. You need to set up a Google API key to use this feature:

1. Using environment variable:
```bash
export GOOGLE_API_KEY=<your_google_api_key>
```

2. Adding to your `.env` file:
```
GOOGLE_API_KEY=<your_google_api_key>
```

You can obtain a Google API key by signing up for Google AI Studio at https://ai.google.dev/.

### Connecting to MCP Server (Optional)

For enhanced natural language capabilities, you can connect the CLI agent to the Model Context Protocol (MCP) server included in this repository:

1. Start the MCP server in a separate terminal:
```bash
cd ../mcp-server-galaxy-py
python -m mcp run main.py
```

2. Configure the CLI agent to use the MCP server:
```bash
export MCP_SERVER_URL=http://localhost:3000/sse
```

3. Or add to your `.env` file:
```
MCP_SERVER_URL=http://localhost:3000/sse
```

When connected to the MCP server, the CLI agent gains access to the full Galaxy API through natural language, allowing for more complex operations and better understanding of bioinformatics queries.

### Command Line Examples

Search for tools:
```bash
galaxy-agent tools search fastq
```

Get tool details:
```bash
galaxy-agent tools details <tool_id> --io
```

Get tool citations:
```bash
galaxy-agent tools citations <tool_id>
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

Upload a file to Galaxy:
```bash
galaxy-agent file upload /path/to/file.fastq --history <history_id>
```

Generate methods section:
```bash
galaxy-agent methods generate <history_id>
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
Galaxy Agent> Generate a methods section for my history 1a2b3c
```

## Methods Generation

One of the most powerful features of the Galaxy CLI Agent is its ability to automatically generate academic methods sections based on your Galaxy histories. This feature:

1. Extracts all tools used in a history with their parameters
2. Collects citation information for each tool
3. Generates a structured methods section suitable for inclusion in academic papers

To use this feature:

```bash
galaxy-agent methods generate <history_id>
```

The resulting methods section will include:
- A general overview of the analysis
- Detailed information about each tool used
- Parameter settings for each tool
- Properly formatted citations

You can save the generated methods section to a file when prompted.

## Architecture

The Galaxy CLI Agent uses a client-server architecture:

1. **Python MCP Server**: Contains core Galaxy API operations for:
   - Tool citations retrieval
   - History details fetching
   - Job details access
   
2. **CLI Agent**: Uses the MCP server and adds higher-level functionality:
   - Methods section generation
   - Interactive natural language interface
   - Command-line argument handling
   - Rich output formatting

This separation of concerns allows:
- Core Galaxy operations to be shared between different clients
- Higher-level features to be built on top of basic operations
- Easier maintenance and extension of the codebase

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