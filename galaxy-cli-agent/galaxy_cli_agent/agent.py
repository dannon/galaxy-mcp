"""Galaxy agent implementation using Pydantic AI."""

from dataclasses import dataclass
import os
from typing import Any, Dict, List, Optional, Union

import httpx
import google.generativeai as genai
from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext
from pydantic_ai.mcp import MCPServerHTTP


# Models for Galaxy objects
class Tool(BaseModel):
    """Galaxy tool model."""

    id: str
    name: str
    description: Optional[str] = None
    version: Optional[str] = None


class History(BaseModel):
    """Galaxy history model."""

    id: str
    name: str
    items_count: int = 0
    size: Optional[int] = None


class Dataset(BaseModel):
    """Galaxy dataset model."""

    id: str
    name: str
    history_id: str
    state: str
    file_type: Optional[str] = None


class Citation(BaseModel):
    """Citation model for Galaxy tools."""

    type: str
    citation: str


class GalaxyResponse(BaseModel):
    """Structured response from Galaxy operations."""

    success: bool
    message: str
    data: Optional[Any] = None


# Dependencies for Galaxy client
@dataclass
class GalaxyDependencies:
    """Dependencies for Galaxy CLI agent."""

    galaxy_url: Optional[str] = None
    api_key: Optional[str] = None
    client: Optional[httpx.AsyncClient] = None
    connected: bool = False


# Configure Google Generative AI if API key is available
api_key = os.environ.get("GOOGLE_API_KEY")
if api_key:
    genai.configure(api_key=api_key)

# Define MCP server URL - explicitly use the SSE endpoint for consistency
MCP_SERVER_BASE_URL = os.environ.get("MCP_SERVER_URL", "http://localhost:3000/sse")

# Try to create MCP server connection
mcp_server = None

try:
    print(f"Creating MCP server connection to: {MCP_SERVER_BASE_URL}")
    # Don't set log_level since it's causing the "Method not found" error
    # FastMCP server might not implement the set_logging_level method
    mcp_server = MCPServerHTTP(
        url=MCP_SERVER_BASE_URL,
        timeout=10,          # More generous timeout
        sse_read_timeout=30, # Longer read timeout
        log_level=None       # Don't set log level to avoid "Method not found" error
    )
    print(f"Successfully created MCP client to: {MCP_SERVER_BASE_URL}")
except Exception as e:
    print(f"Failed to create MCP client: {str(e)}")

if not mcp_server:
    print("Warning: Could not initialize MCP server connection with any endpoint")
    print("Natural language capabilities may be limited without MCP server")

# Prepare MCP servers list
mcp_servers_list = []
if mcp_server:
    mcp_servers_list.append(mcp_server)
    print(f"Adding MCP server to agent: {mcp_server}")

# Create the Galaxy agent with MCP servers
print(f"Setting up agent with {len(mcp_servers_list)} MCP servers")

# Explicitly expose MCP servers for testing
print(f"MCP servers: {mcp_servers_list}")

# Important: mcp_servers must be a properly initialized list in Agent constructor
# For Pydantic-AI >=0.1.30, ensure direct setting of attribute
galaxy_agent = Agent(
    "google-gla:gemini-2.5-flash-preview-04-17",  # Using specific Gemini model version
    deps_type=GalaxyDependencies,
    output_type=GalaxyResponse,
    mcp_servers=mcp_servers_list,  # Pass as parameter
    system_prompt=(
        "You are a Galaxy bioinformatics assistant that helps users interact with "
        "Galaxy instances through a CLI. Your primary function is to interpret natural language "
        "requests and translate them into appropriate Galaxy operations. "
        "\n\n"
        "When users provide natural language queries, analyze them carefully to identify: "
        "1. The core Galaxy operation needed (search, create, list, import, etc.) "
        "2. The Galaxy resource type involved (tools, workflows, histories, datasets) "
        "3. Any parameters or qualifiers specified by the user "
        "4. Any implied bioinformatics context that may be relevant "
        "\n\n"
        "Example interpretations: "
        "- Query: 'Find tools for RNA-seq analysis' → search_tools with query='RNA-seq' "
        "- Query: 'Create a new history called my experiment' → create_history with name='my experiment' "
        "- Query: 'Show me my current histories' → get_histories "
        "- Query: 'I need to analyze bacterial genomes' → search_tools with query related to bacterial genomics "
        "- Query: 'Import the RNA-seq workflow from IWC' → search_iwc_workflows with query='RNA-seq', then import "
        "- Query: 'Generate methods section from history abc123' → generate_methods_section with history_id='abc123' "
        "- Query: 'I want to map my sequencing reads to a reference genome' → search_tools with query focused on mapping/alignment tools "
        "- Query: 'Upload my FASTQ file to Galaxy' → upload_file with appropriate parameters "
        "- Query: 'Find workflows for variant calling' → search_iwc_workflows with query='variant calling' "
        "- Query: 'What tools can I use for differential expression analysis?' → search_tools with query='differential expression' "
        "- Query: 'Show me tools that work with VCF files' → search_tools with query='VCF' "
        "- Query: 'Help me analyze ChIP-seq data' → search_tools with query='ChIP-seq' or related workflows "
        "- Query: 'Get citation information for Bowtie2' → get_tool_citations with tool_id containing 'bowtie2' "
        "\n\n"
        "Bioinformatics domain knowledge: "
        "- Be aware of common file formats (FASTQ, BAM, VCF, BED, GTF, GFF) and suggest appropriate tools "
        "- Recognize common analysis types (variant calling, RNA-seq, metagenomics, ChIP-seq, etc.) "
        "- When a user mentions an organism or data type, use that to guide tool suggestions "
        "- Understand bioinformatics workflows: QC → alignment → processing → visualization → statistics "
        "- Associate key analysis terms with appropriate tools: "
        "  * Trimming/QC: Trimmomatic, FastQC, Cutadapt "
        "  * Alignment: BWA, Bowtie2, HISAT2, STAR "
        "  * Variant calling: FreeBayes, GATK, VarScan "
        "  * RNA-seq: DESeq2, edgeR, featureCounts, Salmon "
        "  * Metagenomics: MetaPhlAn, Kraken, QIIME "
        "  * Assembly: SPAdes, Trinity, Velvet "
        "\n\n"
        "The MCP Server provides these tools that you can use directly:"
        "1. connect(url, api_key): Connect to a Galaxy instance"
        "2. search_tools(query): Search for tools that match the query string"
        "3. get_tool_details(tool_id, io_details): Get detailed information about a specific tool"
        "4. get_tool_citations(tool_id): Get citation information for a tool"
        "5. get_histories(): Get list of all histories"
        "6. create_history(history_name): Create a new history"
        "7. get_history_details(history_id): Get detailed information about a specific history"
        "8. get_iwc_workflows(): Get all available workflows from IWC"
        "9. search_iwc_workflows(query): Search for workflows with a specific query"
        "10. import_workflow_from_iwc(trs_id): Import a workflow by its TRS ID"
        "11. upload_file(path, history_id): Upload a file to Galaxy"
        "12. filter_tools_by_dataset(dataset_type): Find tools that work with a specific dataset type"
        "\n\n"
        "When the MCP server is available, prefer using these direct tool calls through the MCP instead of hardcoded functions."
        "\n\n"
        "Return structured responses that can be easily parsed by the CLI client, but ensure "
        "your underlying reasoning captures the nuance of natural language requests."
        "\n\n"
        "Few-shot learning examples (with reasoning):"
        "\n\n"
        "User: 'I need to analyze RNA-seq data from mouse samples'\n"
        "Reasoning: This query is about RNA-seq, which typically involves quality control, alignment, quantification, and differential expression. They mentioned mouse, so I should focus on tools for eukaryotic/mammalian RNA-seq.\n"
        "Response: search_tools with query='RNA-seq mouse'\n"
        "\n\n"
        "User: 'Create a new history for my ChIP-seq project'\n"
        "Reasoning: The user wants to create a new history container with a specific name for organizing their ChIP-seq analysis.\n"
        "Response: create_history with name='ChIP-seq project'\n"
        "\n\n"
        "User: 'Show me tools for variant calling in human genome data'\n"
        "Reasoning: The user is looking for tools to identify genetic variants from sequencing data, specifically for human samples.\n"
        "Response: search_tools with query='variant calling human'\n"
        "\n\n"
        "User: 'I have fastq files that I need to map to the human genome'\n"
        "Reasoning: This is about read alignment. The input is FASTQ and the reference is human genome. I should suggest mapping/alignment tools.\n"
        "Response: search_tools with query='mapping alignment fastq human'\n"
        "\n\n"
        "User: 'What workflows are available for bacterial genome assembly?'\n"
        "Reasoning: User is looking for ready-to-use workflows for de novo assembly of bacterial genomes.\n"
        "Response: search_iwc_workflows with query='bacterial assembly'"
    ),
)


# Helper function to ensure connection is established
def ensure_connected(ctx: RunContext[GalaxyDependencies]) -> None:
    """Ensure Galaxy connection is established."""
    if not ctx.deps.connected or not ctx.deps.client:
        raise ValueError("Not connected to Galaxy. Use connect command first.")


@galaxy_agent.tool
async def connect(
    ctx: RunContext[GalaxyDependencies], url: str = None, api_key: str = None
) -> GalaxyResponse:
    """
    Connect to a Galaxy instance.

    Args:
        url: Galaxy server URL (optional if environment variables are set)
        api_key: Galaxy API key (optional if environment variables are set)

    Returns:
        Connection status and user information
    """
    try:
        # If URL and API key are not provided, try to get them from environment
        if not url or not api_key:
            env_url = os.environ.get("GALAXY_URL")
            env_api_key = os.environ.get("GALAXY_API_KEY")

            url = url or env_url
            api_key = api_key or env_api_key

            if not url or not api_key:
                return GalaxyResponse(
                    success=False,
                    message="Galaxy URL and API key must be provided either as arguments or environment variables.",
                )

        # If already connected, check if we're using the same credentials
        if (
            ctx.deps.connected
            and ctx.deps.client
            and ctx.deps.galaxy_url == url
            and ctx.deps.api_key == api_key
        ):
            # We're already connected with these credentials
            try:
                # Verify connection is still active
                response = await ctx.deps.client.get("api/users/current")
                response.raise_for_status()
                user_info = response.json()

                return GalaxyResponse(
                    success=True,
                    message="Already connected to Galaxy",
                    data={"user": user_info},
                )
            except:
                # Connection failed, we'll reconnect
                pass

        # Close existing client if we have one but credentials changed
        if ctx.deps.client:
            await ctx.deps.client.aclose()

        # Format URL to ensure it ends with '/'
        galaxy_url = url if url.endswith("/") else f"{url}/"

        # Create a client for this connection
        client = httpx.AsyncClient(
            base_url=galaxy_url,
            headers={"x-api-key": api_key},
            timeout=30.0,
        )

        # Test connection by fetching user info
        response = await client.get("api/users/current")
        response.raise_for_status()
        user_info = response.json()

        # Update dependencies
        ctx.deps.galaxy_url = galaxy_url
        ctx.deps.api_key = api_key
        ctx.deps.client = client
        ctx.deps.connected = True

        return GalaxyResponse(
            success=True,
            message="Successfully connected to Galaxy",
            data={"user": user_info},
        )
    except Exception as e:
        # Close client if it was created
        if "client" in locals():
            await client.aclose()

        return GalaxyResponse(
            success=False,
            message=f"Failed to connect to Galaxy: {str(e)}",
        )


@galaxy_agent.tool
async def search_tools(ctx: RunContext[GalaxyDependencies], query: str) -> GalaxyResponse:
    """
    Search for Galaxy tools by name or function.

    Args:
        query: Search query for tool name or function

    Returns:
        List of tools matching the query
    """
    try:
        ensure_connected(ctx)

        # Search tools using Galaxy API
        response = await ctx.deps.client.get("api/tools", params={"q": query})
        response.raise_for_status()
        tools_data = response.json()

        # Convert to structured tool objects
        tools = []
        for tool in tools_data:
            tools.append(
                Tool(
                    id=tool.get("id", ""),
                    name=tool.get("name", ""),
                    description=tool.get("description", ""),
                    version=tool.get("version", ""),
                )
            )

        return GalaxyResponse(
            success=True,
            message=f"Found {len(tools)} tools matching '{query}'",
            data={"tools": tools},
        )
    except ValueError as e:
        return GalaxyResponse(success=False, message=str(e))
    except Exception as e:
        return GalaxyResponse(
            success=False,
            message=f"Failed to search tools: {str(e)}",
        )


@galaxy_agent.tool
async def get_tool_details(
    ctx: RunContext[GalaxyDependencies], tool_id: str, io_details: bool = False
) -> GalaxyResponse:
    """
    Get detailed information about a specific tool.

    Args:
        tool_id: ID of the tool
        io_details: Whether to include input/output details

    Returns:
        Tool details
    """
    try:
        ensure_connected(ctx)

        # Get tool details from MCP API via Galaxy API
        params = {}
        if io_details:
            params["io_details"] = "true"

        response = await ctx.deps.client.get(f"api/tools/{tool_id}", params=params)
        response.raise_for_status()
        tool_info = response.json()

        return GalaxyResponse(
            success=True,
            message=f"Successfully retrieved details for tool '{tool_id}'",
            data={"tool": tool_info},
        )
    except ValueError as e:
        return GalaxyResponse(success=False, message=str(e))
    except Exception as e:
        return GalaxyResponse(
            success=False,
            message=f"Failed to get tool details: {str(e)}",
        )


@galaxy_agent.tool
async def get_histories(ctx: RunContext[GalaxyDependencies]) -> GalaxyResponse:
    """
    Get list of user histories.

    Returns:
        List of histories
    """
    try:
        ensure_connected(ctx)

        # Get histories from Galaxy API
        response = await ctx.deps.client.get("api/histories", params={"view": "summary"})
        response.raise_for_status()
        histories_data = response.json()

        # Convert to structured history objects
        histories = []
        for history in histories_data:
            histories.append(
                History(
                    id=history.get("id", ""),
                    name=history.get("name", ""),
                    items_count=history.get("count", 0),
                    size=history.get("size", None),
                )
            )

        return GalaxyResponse(
            success=True,
            message=f"Found {len(histories)} histories",
            data={"histories": histories},
        )
    except ValueError as e:
        return GalaxyResponse(success=False, message=str(e))
    except Exception as e:
        return GalaxyResponse(
            success=False,
            message=f"Failed to get histories: {str(e)}",
        )


@galaxy_agent.tool
async def create_history(ctx: RunContext[GalaxyDependencies], name: str) -> GalaxyResponse:
    """
    Create a new history with the given name.

    Args:
        name: Name for the new history

    Returns:
        Created history details
    """
    try:
        ensure_connected(ctx)

        # Create history using Galaxy API
        response = await ctx.deps.client.post("api/histories", json={"name": name})
        response.raise_for_status()
        history_data = response.json()

        history = History(
            id=history_data.get("id", ""),
            name=history_data.get("name", ""),
            items_count=history_data.get("count", 0),
            size=history_data.get("size", None),
        )

        return GalaxyResponse(
            success=True,
            message=f"Created new history '{name}'",
            data={"history": history},
        )
    except ValueError as e:
        return GalaxyResponse(success=False, message=str(e))
    except Exception as e:
        return GalaxyResponse(
            success=False,
            message=f"Failed to create history: {str(e)}",
        )


@galaxy_agent.tool
async def get_iwc_workflows(ctx: RunContext[GalaxyDependencies]) -> GalaxyResponse:
    """
    Fetch all workflows from the IWC (Interactive Workflow Composer).

    Returns:
        Complete workflow manifest from IWC
    """
    try:
        # This doesn't require Galaxy connection as it's from a public URL
        async with httpx.AsyncClient() as client:
            response = await client.get("https://iwc.galaxyproject.org/workflow_manifest.json")
            response.raise_for_status()
            data = response.json()
            workflows = data[0]["workflows"]

        return GalaxyResponse(
            success=True,
            message=f"Found {len(workflows)} workflows in IWC",
            data={"workflows": workflows},
        )
    except Exception as e:
        return GalaxyResponse(
            success=False,
            message=f"Failed to fetch IWC workflows: {str(e)}",
        )


@galaxy_agent.tool
async def search_iwc_workflows(ctx: RunContext[GalaxyDependencies], query: str) -> GalaxyResponse:
    """
    Search for workflows in the IWC manifest.

    Args:
        query: Search query (matches against name, description, and tags)

    Returns:
        List of matching workflows
    """
    try:
        # Get all workflows first
        all_workflows_response = await get_iwc_workflows(ctx)
        if not all_workflows_response.success:
            return all_workflows_response

        workflows = all_workflows_response.data["workflows"]
        query = query.lower()

        # Filter workflows based on the search query
        results = []
        for workflow in workflows:
            # Check if query matches name, description or tags
            name = workflow.get("definition", {}).get("name", "").lower()
            description = workflow.get("definition", {}).get("annotation", "").lower()
            tags = [tag.lower() for tag in workflow.get("definition", {}).get("tags", [])]

            if (
                query in name
                or query in description
                or (tags and any(query in tag for tag in tags))
            ):
                results.append(workflow)

        return GalaxyResponse(
            success=True,
            message=f"Found {len(results)} workflows matching '{query}'",
            data={"workflows": results},
        )
    except Exception as e:
        return GalaxyResponse(
            success=False,
            message=f"Failed to search IWC workflows: {str(e)}",
        )


@galaxy_agent.tool
async def import_workflow_from_iwc(
    ctx: RunContext[GalaxyDependencies], trs_id: str
) -> GalaxyResponse:
    """
    Import a workflow from IWC to the user's Galaxy instance.

    Args:
        trs_id: TRS ID of the workflow in the IWC manifest

    Returns:
        Imported workflow information
    """
    try:
        ensure_connected(ctx)

        # Get the workflow manifest
        all_workflows_response = await get_iwc_workflows(ctx)
        if not all_workflows_response.success:
            return all_workflows_response

        workflows = all_workflows_response.data["workflows"]

        # Find the specified workflow
        workflow = None
        for wf in workflows:
            if wf.get("trsID") == trs_id:
                workflow = wf
                break

        if not workflow:
            return GalaxyResponse(
                success=False,
                message=f"Workflow with trsID {trs_id} not found in IWC manifest",
            )

        # Extract the workflow definition
        workflow_definition = workflow.get("definition")
        if not workflow_definition:
            return GalaxyResponse(
                success=False,
                message=f"No definition found for workflow with trsID {trs_id}",
            )

        # Import the workflow into Galaxy
        response = await ctx.deps.client.post(
            "api/workflows", json={"workflow": workflow_definition}
        )
        response.raise_for_status()
        imported_workflow = response.json()

        return GalaxyResponse(
            success=True,
            message=f"Successfully imported workflow '{workflow_definition.get('name')}'",
            data={"imported_workflow": imported_workflow},
        )
    except ValueError as e:
        return GalaxyResponse(success=False, message=str(e))
    except Exception as e:
        return GalaxyResponse(
            success=False,
            message=f"Failed to import workflow from IWC: {str(e)}",
        )


@galaxy_agent.tool
async def upload_file(
    ctx: RunContext[GalaxyDependencies], path: str, history_id: Optional[str] = None
) -> GalaxyResponse:
    """
    Upload a local file to Galaxy.

    Args:
        path: Path to local file
        history_id: Target history ID (optional)

    Returns:
        Upload status
    """
    try:
        ensure_connected(ctx)

        # Check if file exists
        if not os.path.exists(path):
            return GalaxyResponse(
                success=False,
                message=f"File not found: {path}",
            )

        # Get the file name from the path
        file_name = os.path.basename(path)

        # Read file content
        with open(path, "rb") as f:
            file_content = f.read()

        # Prepare form data
        files = {"files_0|file_data": (file_name, file_content)}
        payload = {"history_id": history_id} if history_id else {}

        # Upload file to Galaxy
        response = await ctx.deps.client.post("api/tools/fetch", data=payload, files=files)
        response.raise_for_status()
        upload_result = response.json()

        return GalaxyResponse(
            success=True,
            message=f"Successfully uploaded file '{file_name}'",
            data={"upload_result": upload_result},
        )
    except ValueError as e:
        return GalaxyResponse(success=False, message=str(e))
    except Exception as e:
        return GalaxyResponse(
            success=False,
            message=f"Failed to upload file: {str(e)}",
        )


@galaxy_agent.tool
async def get_tool_citations(ctx: RunContext[GalaxyDependencies], tool_id: str) -> GalaxyResponse:
    """
    Get citation information for a specific tool.

    Args:
        tool_id: ID of the tool

    Returns:
        Tool citation information
    """
    try:
        ensure_connected(ctx)

        # Get tool details which include citations
        response = await ctx.deps.client.get(f"api/tools/{tool_id}")
        response.raise_for_status()
        tool_info = response.json()

        # Extract citation information
        citations = tool_info.get("citations", [])
        formatted_citations = []

        for citation in citations:
            formatted_citations.append(
                Citation(
                    type=citation.get("type", "unknown"), citation=citation.get("citation", "")
                )
            )

        return GalaxyResponse(
            success=True,
            message=f"Found {len(formatted_citations)} citations for tool '{tool_id}'",
            data={
                "tool_name": tool_info.get("name", tool_id),
                "tool_version": tool_info.get("version", "unknown"),
                "citations": formatted_citations,
            },
        )
    except ValueError as e:
        return GalaxyResponse(success=False, message=str(e))
    except Exception as e:
        return GalaxyResponse(
            success=False,
            message=f"Failed to get tool citations: {str(e)}",
        )


@galaxy_agent.tool
async def get_history_details(
    ctx: RunContext[GalaxyDependencies], history_id: str
) -> GalaxyResponse:
    """
    Get detailed information about a specific history, including datasets.

    Args:
        history_id: ID of the history

    Returns:
        History details with datasets
    """
    try:
        ensure_connected(ctx)

        # Get history details and contents from the API
        response = await ctx.deps.client.get(
            f"api/histories/{history_id}", params={"view": "detailed"}
        )
        response.raise_for_status()
        history_info = response.json()

        # Get history contents
        contents_response = await ctx.deps.client.get(
            f"api/histories/{history_id}/contents", params={"view": "detailed"}
        )
        contents_response.raise_for_status()
        contents = contents_response.json()

        return GalaxyResponse(
            success=True,
            message=f"Successfully retrieved details for history '{history_info.get('name')}'",
            data={"history": history_info, "contents": contents},
        )
    except ValueError as e:
        return GalaxyResponse(success=False, message=str(e))
    except Exception as e:
        return GalaxyResponse(
            success=False,
            message=f"Failed to get history details: {str(e)}",
        )


@galaxy_agent.tool
async def get_job_details(ctx: RunContext[GalaxyDependencies], job_id: str) -> GalaxyResponse:
    """
    Get detailed information about a specific job.

    Args:
        job_id: ID of the job

    Returns:
        Job details with tool information
    """
    try:
        ensure_connected(ctx)

        # Get job details from the API
        response = await ctx.deps.client.get(f"api/jobs/{job_id}")
        response.raise_for_status()
        job_info = response.json()

        return GalaxyResponse(
            success=True,
            message=f"Successfully retrieved details for job '{job_id}'",
            data={"job": job_info},
        )
    except ValueError as e:
        return GalaxyResponse(success=False, message=str(e))
    except Exception as e:
        return GalaxyResponse(
            success=False,
            message=f"Failed to get job details: {str(e)}",
        )


@galaxy_agent.tool
async def generate_methods_section(
    ctx: RunContext[GalaxyDependencies], history_id: str
) -> GalaxyResponse:
    """
    Generate a methods section based on tools used in a history.

    Args:
        history_id: ID of the history

    Returns:
        Formatted methods section with citations
    """
    try:
        ensure_connected(ctx)

        # Get history details
        history_response = await get_history_details(ctx, history_id)
        if not history_response.success:
            return history_response

        history_info = history_response.data["history"]
        contents = history_response.data["contents"]

        # Filter for successful jobs
        jobs_info = []
        tools_used = []
        citations = []

        # Process all datasets in history
        for dataset in contents:
            # Skip collections and datasets without creating_job
            if dataset.get("history_content_type") != "dataset" or not dataset.get("creating_job"):
                continue

            # Only include successfully completed jobs/tools
            if dataset.get("state") != "ok":
                continue

            job_id = dataset.get("creating_job")
            tool_id = dataset.get("tool_id")

            # Skip if we've already processed this tool
            if tool_id in [t.get("id") for t in tools_used]:
                continue

            # Get tool details and citations
            tool_response = await get_tool_details(ctx, tool_id)
            if tool_response.success:
                tool_info = tool_response.data["tool"]
                tools_used.append(tool_info)

                # Get citations
                citations_response = await get_tool_citations(ctx, tool_id)
                if citations_response.success and citations_response.data["citations"]:
                    citations.extend(citations_response.data["citations"])

            # Get job details
            job_response = await get_job_details(ctx, job_id)
            if job_response.success:
                jobs_info.append(job_response.data["job"])

        # Organize the data for methods generation
        methods_data = {
            "history_name": history_info.get("name", "Unknown history"),
            "tools": tools_used,
            "jobs": jobs_info,
            "citations": citations,
        }

        # Generate methods text that includes:
        # 1. A general overview of the analysis
        # 2. A description of each tool and its parameters
        # 3. Properly formatted citations
        methods_text = (
            f"# Methods\n\n"
            f"## Overview\n\n"
            f"The analysis was performed using Galaxy ({history_info.get('nice_size', 'unknown')} of data). "
            f"The history '{history_info.get('name')}' contains {len(contents)} datasets "
            f"generated using {len(tools_used)} distinct tools.\n\n"
            f"## Analysis Details\n\n"
        )

        # Add details for each tool
        for tool in tools_used:
            methods_text += f"### {tool.get('name')} (version {tool.get('version', 'unknown')})\n\n"
            methods_text += f"{tool.get('description', 'No description available')}\n\n"

            # Add parameter details if available
            for job in jobs_info:
                if job.get("tool_id") == tool.get("id"):
                    methods_text += "**Parameters used:**\n\n"
                    params = job.get("params", {})
                    for param_name, param_value in params.items():
                        if param_name not in [
                            "__workflow_invocation_uuid__",
                            "__rerun_remap_job_id__",
                        ]:
                            methods_text += f"- {param_name}: {param_value}\n"
                    methods_text += "\n"
                    break

        # Add citations section
        if citations:
            methods_text += "## References\n\n"
            for i, citation in enumerate(citations, 1):
                methods_text += f"{i}. {citation.citation}\n"

        return GalaxyResponse(
            success=True,
            message=f"Successfully generated methods section for history '{history_info.get('name')}'",
            data={"methods_text": methods_text, "methods_data": methods_data},
        )
    except ValueError as e:
        return GalaxyResponse(success=False, message=str(e))
    except Exception as e:
        return GalaxyResponse(
            success=False,
            message=f"Failed to generate methods section: {str(e)}",
        )
