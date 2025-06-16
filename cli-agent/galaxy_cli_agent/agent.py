"""Galaxy agent implementation using Pydantic AI and MCP server."""

import os
from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel
from pydantic_ai import Agent, RunContext
from pydantic_ai.mcp import MCPServerHTTP


# Models for structured responses
class GalaxyResponse(BaseModel):
    """Structured response from Galaxy operations via MCP server."""

    success: bool
    message: str
    data: Any | None = None
    operation: str | None = None


# Dependencies for Galaxy client (simplified - MCP server handles actual connections)
@dataclass
class GalaxyDependencies:
    """Dependencies for Galaxy CLI agent."""

    # We don't need actual Galaxy connection details here since MCP server handles that
    mcp_available: bool = False


# Configure MCP server connection
MCP_SERVER_BASE_URL = os.environ.get("MCP_SERVER_URL", "http://localhost:3000/sse")

# Try to create MCP server connection
mcp_server = None
try:
    mcp_server = MCPServerHTTP(
        url=MCP_SERVER_BASE_URL,
        timeout=10,
        sse_read_timeout=30,
    )
    print(f"MCP server connection configured: {MCP_SERVER_BASE_URL}")
except Exception as e:
    print(f"Failed to configure MCP server: {e}")

# Prepare MCP servers list
mcp_servers_list = []
if mcp_server:
    mcp_servers_list.append(mcp_server)

# Create the Galaxy agent focused purely on natural language interpretation
galaxy_agent = Agent(
    "gemini-2.0-flash-exp",  # Use Pydantic AI's model handling
    deps_type=GalaxyDependencies,
    output_type=GalaxyResponse,
    mcp_servers=mcp_servers_list,
    system_prompt=(
        "You are a Galaxy bioinformatics assistant that helps users interact with "
        "Galaxy instances through natural language. Your role is to interpret user requests "
        "and translate them into appropriate Galaxy operations using the available MCP tools.\n\n"
        "IMPORTANT: You have access to a full Galaxy MCP server that provides all Galaxy "
        "operations. Use the MCP tools directly rather than implementing Galaxy operations "
        "yourself.\n\n"
        "Available MCP tools include:\n"
        "- connect(url, api_key): Connect to Galaxy\n"
        "- search_tools(query): Search for tools\n"
        "- get_tool_details(tool_id, io_details): Get tool information\n"
        "- get_tool_citations(tool_id): Get tool citations\n"
        "- get_histories(): List user histories\n"
        "- create_history(name): Create new history\n"
        "- get_history_details(history_id): Get history details\n"
        "- get_job_details(job_id): Get job information\n"
        "- run_tool(history_id, tool_id, inputs): Execute tools\n"
        "- upload_file(path, history_id): Upload files\n"
        "- get_iwc_workflows(): Get IWC workflows\n"
        "- search_iwc_workflows(query): Search workflows\n"
        "- import_workflow_from_iwc(trs_id): Import workflows\n"
        "- filter_tools_by_dataset(dataset_type): Find tools for data types\n\n"
        "When users provide natural language queries, analyze them to identify:\n"
        "1. The core Galaxy operation needed\n"
        "2. The resource type (tools, workflows, histories, datasets)\n"
        "3. Any parameters or qualifiers\n"
        "4. Bioinformatics context\n\n"
        "Bioinformatics domain knowledge:\n"
        "- Common file formats: FASTQ, BAM, VCF, BED, GTF, GFF\n"
        "- Analysis types: RNA-seq, variant calling, metagenomics, ChIP-seq\n"
        "- Workflow stages: QC → alignment → processing → analysis\n"
        "- Key tools: BWA, Bowtie2, STAR, GATK, DESeq2, FastQC, etc.\n\n"
        "Example interpretations:\n"
        "- 'Find RNA-seq tools' → search_tools with query='RNA-seq'\n"
        "- 'Create analysis history' → create_history with name='analysis'\n"
        "- 'Import variant calling workflow' → search_iwc_workflows + import\n"
        "- 'Generate methods from history abc123' → generate_methods_section\n\n"
        "Always return structured GalaxyResponse objects with:\n"
        "- success: boolean indicating if operation succeeded\n"
        "- message: human-readable description\n"
        "- data: relevant results from MCP tools\n"
        "- operation: the type of operation performed"
    ),
)


@galaxy_agent.tool
async def generate_methods_section(
    ctx: RunContext[GalaxyDependencies], history_id: str
) -> GalaxyResponse:
    """
    Generate an academic methods section from a Galaxy history.

    This is the only Galaxy-specific tool that's not duplicated from MCP server,
    as it's a higher-level analysis function.

    Args:
        history_id: ID of the Galaxy history to analyze

    Returns:
        Generated methods section with citations
    """
    try:
        # This function uses multiple MCP tools to build a methods section
        # It will be implemented to:
        # 1. Get history details via MCP
        # 2. Get job details for each step via MCP
        # 3. Get tool citations via MCP
        # 4. Generate formatted methods text

        return GalaxyResponse(
            success=True,
            message="Methods generation is not yet implemented in refactored version",
            operation="generate_methods_section",
            data={
                "status": "pending_implementation",
                "note": (
                    "This will use MCP tools: get_history_details, get_job_details, "
                    "get_tool_citations"
                ),
            },
        )

    except Exception as e:
        return GalaxyResponse(
            success=False,
            message=f"Failed to generate methods section: {str(e)}",
            operation="generate_methods_section",
        )


# Helper function to create dependencies
def create_dependencies() -> GalaxyDependencies:
    """Create Galaxy dependencies with MCP server availability check."""
    return GalaxyDependencies(mcp_available=len(mcp_servers_list) > 0)


# Expose key components for CLI
__all__ = [
    "galaxy_agent",
    "GalaxyDependencies",
    "GalaxyResponse",
    "create_dependencies",
    "MCP_SERVER_BASE_URL",
]
