"""Command-line interface for the Galaxy CLI Agent."""

import asyncio
import os
from typing import List, Optional

import httpx
from dotenv import find_dotenv, load_dotenv
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from galaxy_cli_agent.agent import GalaxyDependencies, galaxy_agent, GalaxyResponse

# Create Typer app and console for rich output
app = typer.Typer(
    name="galaxy-agent",
    help="CLI agent for interacting with Galaxy using Pydantic AI",
    add_completion=False,
)
console = Console()

# Create sub-commands
tools_app = typer.Typer(help="Tools management operations")
workflow_app = typer.Typer(help="Workflow management operations")
history_app = typer.Typer(help="History management operations")
file_app = typer.Typer(help="File operations")

app.add_typer(tools_app, name="tools")
app.add_typer(workflow_app, name="workflow")
app.add_typer(history_app, name="history")
app.add_typer(file_app, name="file")


# Helper function to load environment variables
def load_env_vars() -> tuple[Optional[str], Optional[str]]:
    """Load Galaxy URL and API key from environment variables or .env file."""
    # Try to load environment variables from .env file
    dotenv_path = find_dotenv(usecwd=True)
    if dotenv_path:
        load_dotenv(dotenv_path)

    return os.environ.get("GALAXY_URL"), os.environ.get("GALAXY_API_KEY")


# Helper function to initialize Galaxy dependencies
def init_dependencies() -> GalaxyDependencies:
    """Initialize Galaxy dependencies from environment variables or .env file."""
    galaxy_url, api_key = load_env_vars()
    
    deps = GalaxyDependencies(
        galaxy_url=galaxy_url,
        api_key=api_key,
        connected=False,
    )
    
    return deps


# Helper function to handle responses
def handle_response(response: GalaxyResponse) -> None:
    """Handle Galaxy agent response and display it nicely."""
    if response.success:
        console.print(Panel(response.message, title="Success", style="green"))
        
        # Handle different data types
        if response.data:
            if "user" in response.data:
                user = response.data["user"]
                console.print(f"Connected as: {user.get('username', 'Unknown user')}")
            
            elif "tools" in response.data:
                tools = response.data["tools"]
                if tools:
                    table = Table(title="Galaxy Tools")
                    table.add_column("ID", style="cyan")
                    table.add_column("Name", style="green")
                    table.add_column("Description")
                    
                    for tool in tools:
                        table.add_row(
                            tool.id,
                            tool.name,
                            tool.description or "No description",
                        )
                    console.print(table)
            
            elif "histories" in response.data:
                histories = response.data["histories"]
                if histories:
                    table = Table(title="Galaxy Histories")
                    table.add_column("ID", style="cyan")
                    table.add_column("Name", style="green")
                    table.add_column("Items", style="blue")
                    
                    for history in histories:
                        table.add_row(
                            history.id,
                            history.name,
                            str(history.items_count),
                        )
                    console.print(table)
            
            elif "history" in response.data:
                history = response.data["history"]
                console.print(f"History ID: {history.id}")
                console.print(f"Name: {history.name}")
            
            elif "workflows" in response.data:
                workflows = response.data["workflows"]
                if workflows:
                    table = Table(title="Galaxy Workflows")
                    table.add_column("TRS ID", style="cyan")
                    table.add_column("Name", style="green")
                    
                    for workflow in workflows:
                        table.add_row(
                            workflow.get("trsID", "Unknown"),
                            workflow.get("definition", {}).get("name", "Unnamed workflow"),
                        )
                    console.print(table)
            
            elif "imported_workflow" in response.data:
                workflow = response.data["imported_workflow"]
                console.print(f"Workflow ID: {workflow.get('id')}")
                console.print(f"Name: {workflow.get('name')}")
                
            elif "upload_result" in response.data:
                upload = response.data["upload_result"]
                console.print(f"Upload job ID: {upload.get('jobs', [{}])[0].get('id', 'Unknown')}")
                console.print(f"Status: {upload.get('jobs', [{}])[0].get('state', 'Unknown')}")
    else:
        console.print(Panel(response.message, title="Error", style="red"))


@app.command("connect")
def connect_command(
    url: str = typer.Option(None, help="Galaxy server URL"),
    api_key: str = typer.Option(None, help="Galaxy API key"),
) -> None:
    """Connect to Galaxy server."""
    # If parameters are not provided, try to load from environment
    if not url or not api_key:
        env_url, env_api_key = load_env_vars()
        url = url or env_url
        api_key = api_key or env_api_key
        
        if not url or not api_key:
            console.print(
                "Error: Galaxy URL and API key must be provided either as command arguments, "
                "environment variables, or in a .env file.",
                style="red",
            )
            return
    
    # Initialize dependencies
    deps = GalaxyDependencies()
    
    # Run connect tool
    response = asyncio.run(galaxy_agent.run_sync(
        "Connect to Galaxy",
        deps=deps,
    ))
    
    # Handle response
    handle_response(response.output)


@tools_app.command("search")
def search_tools_command(query: str = typer.Argument(..., help="Search query")) -> None:
    """Search for Galaxy tools."""
    # Initialize dependencies
    deps = init_dependencies()
    
    # Run search_tools tool
    response = asyncio.run(galaxy_agent.run_sync(
        f"Search for Galaxy tools matching: {query}",
        deps=deps,
    ))
    
    # Handle response
    handle_response(response.output)


@tools_app.command("details")
def tool_details_command(
    tool_id: str = typer.Argument(..., help="Tool ID"),
    io_details: bool = typer.Option(False, "--io", help="Include input/output details"),
) -> None:
    """Get detailed information about a specific tool."""
    # Initialize dependencies
    deps = init_dependencies()
    
    # Run get_tool_details tool
    response = asyncio.run(galaxy_agent.run_sync(
        f"Get details for tool: {tool_id} with IO details: {io_details}",
        deps=deps,
    ))
    
    # Handle response
    handle_response(response.output)


@history_app.command("list")
def list_histories_command() -> None:
    """List all histories in Galaxy."""
    # Initialize dependencies
    deps = init_dependencies()
    
    # Run get_histories tool
    response = asyncio.run(galaxy_agent.run_sync(
        "List all histories",
        deps=deps,
    ))
    
    # Handle response
    handle_response(response.output)


@history_app.command("create")
def create_history_command(name: str = typer.Argument(..., help="History name")) -> None:
    """Create a new history."""
    # Initialize dependencies
    deps = init_dependencies()
    
    # Run create_history tool
    response = asyncio.run(galaxy_agent.run_sync(
        f"Create a new history named: {name}",
        deps=deps,
    ))
    
    # Handle response
    handle_response(response.output)


@workflow_app.command("list")
def list_workflows_command() -> None:
    """List all workflows from IWC."""
    # Initialize dependencies
    deps = init_dependencies()
    
    # Run get_iwc_workflows tool
    response = asyncio.run(galaxy_agent.run_sync(
        "List all workflows from IWC",
        deps=deps,
    ))
    
    # Handle response
    handle_response(response.output)


@workflow_app.command("search")
def search_workflows_command(query: str = typer.Argument(..., help="Search query")) -> None:
    """Search for workflows in IWC."""
    # Initialize dependencies
    deps = init_dependencies()
    
    # Run search_iwc_workflows tool
    response = asyncio.run(galaxy_agent.run_sync(
        f"Search for workflows matching: {query}",
        deps=deps,
    ))
    
    # Handle response
    handle_response(response.output)


@workflow_app.command("import")
def import_workflow_command(trs_id: str = typer.Argument(..., help="TRS ID of the workflow")) -> None:
    """Import a workflow from IWC to Galaxy."""
    # Initialize dependencies
    deps = init_dependencies()
    
    # Run import_workflow_from_iwc tool
    response = asyncio.run(galaxy_agent.run_sync(
        f"Import workflow with TRS ID: {trs_id}",
        deps=deps,
    ))
    
    # Handle response
    handle_response(response.output)


@file_app.command("upload")
def upload_file_command(
    path: str = typer.Argument(..., help="Path to local file"),
    history_id: str = typer.Option(None, "--history", "-h", help="Target history ID"),
) -> None:
    """Upload a file to Galaxy."""
    # Initialize dependencies
    deps = init_dependencies()
    
    # Run upload_file tool
    response = asyncio.run(galaxy_agent.run_sync(
        f"Upload file: {path} to history: {history_id or 'default history'}",
        deps=deps,
    ))
    
    # Handle response
    handle_response(response.output)


@app.command("interact")
def interact_command() -> None:
    """Start interactive mode with natural language interface."""
    # Initialize dependencies
    deps = init_dependencies()
    
    console.print(Panel(
        "Starting interactive mode. Type 'exit' to quit.",
        title="Galaxy Agent Interactive Mode",
        style="blue",
    ))
    
    while True:
        try:
            # Get user input
            user_input = typer.prompt("\n[bold cyan]Galaxy Agent>[/] ")
            
            # Check for exit command
            if user_input.lower() in ("exit", "quit", "bye"):
                console.print("Goodbye!", style="green")
                break
            
            # Run agent with user input
            console.print("Processing...", style="yellow")
            response = asyncio.run(galaxy_agent.run_sync(
                user_input,
                deps=deps,
            ))
            
            # Handle response
            handle_response(response.output)
            
        except KeyboardInterrupt:
            console.print("\nGoodbye!", style="green")
            break
        except Exception as e:
            console.print(f"Error: {str(e)}", style="red")


if __name__ == "__main__":
    app()