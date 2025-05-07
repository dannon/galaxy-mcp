"""Galaxy agent implementation using Pydantic AI."""

from dataclasses import dataclass
import os
from typing import Any, Dict, List, Optional, Union

import httpx
from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext


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


# Create the Galaxy agent
galaxy_agent = Agent(
    "anthropic:claude-3-5-sonnet-latest",  # Can be configured
    deps_type=GalaxyDependencies,
    output_type=GalaxyResponse,
    system_prompt=(
        "You are a Galaxy bioinformatics assistant that helps users interact with "
        "Galaxy instances through a CLI. You can search tools, manage workflows, "
        "create histories, and run analyses. Return structured responses that can "
        "be easily parsed by the CLI client."
    ),
)


# Helper function to ensure connection is established
def ensure_connected(ctx: RunContext[GalaxyDependencies]) -> None:
    """Ensure Galaxy connection is established."""
    if not ctx.deps.connected or not ctx.deps.client:
        raise ValueError("Not connected to Galaxy. Use connect command first.")


@galaxy_agent.tool
async def connect(
    ctx: RunContext[GalaxyDependencies], url: str, api_key: str
) -> GalaxyResponse:
    """
    Connect to a Galaxy instance.

    Args:
        url: Galaxy server URL
        api_key: Galaxy API key

    Returns:
        Connection status and user information
    """
    try:
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

        # Get tool details from Galaxy API
        params = {"io_details": "true" if io_details else "false"}
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
async def search_iwc_workflows(
    ctx: RunContext[GalaxyDependencies], query: str
) -> GalaxyResponse:
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
    ctx: RunContext[GalaxyDependencies], 
    path: str, 
    history_id: Optional[str] = None
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
        response = await ctx.deps.client.post(
            "api/tools/fetch",
            data=payload,
            files=files
        )
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