"""Command-line interface for the Galaxy CLI Agent."""

import asyncio
import os
from typing import Optional

import httpx
from dotenv import find_dotenv, load_dotenv
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.markdown import Markdown

from galaxy_cli_agent.agent import (
    galaxy_agent, 
    GalaxyDependencies, 
    GalaxyResponse, 
    create_dependencies,
    MCP_SERVER_BASE_URL
)

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
methods_app = typer.Typer(help="Methods and citations operations")

app.add_typer(tools_app, name="tools")
app.add_typer(workflow_app, name="workflow")
app.add_typer(history_app, name="history")
app.add_typer(file_app, name="file")
app.add_typer(methods_app, name="methods")


# Helper function to load environment variables
def load_env_vars() -> None:
    """Load environment variables from .env file if present."""
    dotenv_path = find_dotenv(usecwd=True)
    if dotenv_path:
        load_dotenv(dotenv_path)


# Helper function to initialize Galaxy dependencies (simplified)
def init_dependencies() -> GalaxyDependencies:
    """Initialize Galaxy dependencies."""
    load_env_vars()
    return create_dependencies()


# Helper function to run agent commands
async def run_agent_command_async(prompt: str, deps: GalaxyDependencies, error_prefix: str = "Error") -> Optional[GalaxyResponse]:
    """Run an agent command with standardized error handling asynchronously."""
    try:
        # Try to run with MCP servers
        try:
            # Run MCP servers inside an async context manager
            async with galaxy_agent.run_mcp_servers():
                response = await galaxy_agent.run(prompt, deps=deps)
                # The agent.run() returns an AgentRunResult object which has an 'output' attribute
                # that contains the actual GalaxyResponse
                return response.output
        except Exception as mcp_error:
            # Check if it's the "Method not found" error for set_logging_level
            error_str = str(mcp_error)
            if "Method not found" in error_str:
                console.print("Warning: MCP server doesn't support certain methods. Falling back to direct agent use.", style="yellow")
                # Fall back to running the agent without the MCP context manager
                response = await galaxy_agent.run(prompt, deps=deps)
                return response.output
            else:
                # Re-raise other errors
                raise
    except Exception as e:
        console.print(f"{error_prefix}: {str(e)}", style="red")
        import traceback
        console.print(traceback.format_exc(), style="dim")
        return None

def run_agent_command(prompt: str, deps: GalaxyDependencies, error_prefix: str = "Error") -> None:
    """Run an agent command with standardized error handling."""
    try:
        # Create a new event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Run the async function and get the response
        response = loop.run_until_complete(run_agent_command_async(prompt, deps, error_prefix))
        
        # Close the loop
        loop.close()
        
        # Handle the response if it's not None
        if response:
            handle_response(response)
    except Exception as e:
        console.print(f"{error_prefix}: {str(e)}", style="red")
        import traceback
        console.print(traceback.format_exc(), style="dim")


# Helper function to handle responses
def handle_response(response: GalaxyResponse) -> None:
    """Handle Galaxy agent response and display it nicely."""
    if response.success:
        # Make sure to show the message content with proper formatting
        if response.message:
            panel_content = response.message
            console.print(Panel(panel_content, title="Success", style="green"))

        # Handle different data types
        if response.data:
            # Print the data in a nice format
            console.print("\n[bold]Response Data:[/bold]")
            
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

            elif "methods_text" in response.data:
                methods_text = response.data["methods_text"]
                console.print(Markdown(methods_text))

                # Offer to save to file
                save_to_file = typer.confirm("Save methods section to a file?")
                if save_to_file:
                    file_path = typer.prompt("Enter file path")
                    try:
                        with open(file_path, "w") as f:
                            f.write(methods_text)
                        console.print(f"Methods section saved to {file_path}", style="green")
                    except Exception as e:
                        console.print(f"Error saving to file: {str(e)}", style="red")
            else:
                # For any other data type, display raw data
                for key, value in response.data.items():
                    console.print(f"[bold]{key}:[/bold] {value}")
    else:
        # For error responses
        error_message = response.message if response.message else "Unknown error occurred"
        console.print(Panel(error_message, title="Error", style="red"))
        
        # Show data if available even for error responses
        if response.data:
            console.print("\n[bold]Error Details:[/bold]")
            for key, value in response.data.items():
                console.print(f"[bold]{key}:[/bold] {value}")


@app.command("connect")
def connect_command(
    url: str = typer.Option(None, help="Galaxy server URL"),
    api_key: str = typer.Option(None, help="Galaxy API key"),
) -> None:
    """Connect to Galaxy server."""
    # If parameters are not provided, try to load from environment
    if not url or not api_key:
        env_url, env_api_key, google_api_key = load_env_vars()
        url = url or env_url
        api_key = api_key or env_api_key

        # Set the Google API key for Gemini
        if google_api_key:
            os.environ["GOOGLE_API_KEY"] = google_api_key
        else:
            console.print(
                "Warning: GOOGLE_API_KEY not found in environment variables or .env file. "
                "This is required for the Gemini model to function.",
                style="yellow",
            )

        if not url or not api_key:
            console.print(
                "Error: Galaxy URL and API key must be provided either as command arguments, "
                "environment variables, or in a .env file.",
                style="red",
            )
            return

    # Initialize dependencies
    deps = GalaxyDependencies()

    # Run connect tool using the helper function
    run_agent_command("Connect to Galaxy", deps, "Error connecting to Galaxy")


@tools_app.command("search")
def search_tools_command(query: str = typer.Argument(..., help="Search query")) -> None:
    """Search for Galaxy tools."""
    # Initialize dependencies
    deps = init_dependencies()

    # Run search_tools tool using the helper function
    run_agent_command(f"Search for Galaxy tools matching: {query}", deps, "Error searching tools")


@tools_app.command("details")
def tool_details_command(
    tool_id: str = typer.Argument(..., help="Tool ID"),
    io_details: bool = typer.Option(False, "--io", help="Include input/output details"),
) -> None:
    """Get detailed information about a specific tool."""
    # Initialize dependencies
    deps = init_dependencies()

    # Run get_tool_details tool using the helper function
    run_agent_command(
        f"Get details for tool: {tool_id} with IO details: {io_details}",
        deps,
        "Error retrieving tool details",
    )


@tools_app.command("citations")
def tool_citations_command(
    tool_id: str = typer.Argument(..., help="Tool ID"),
) -> None:
    """Get citation information for a specific tool."""
    # Initialize dependencies
    deps = init_dependencies()

    # Run get_tool_citations tool using the helper function
    run_agent_command(f"Get citations for tool: {tool_id}", deps, "Error retrieving tool citations")


@history_app.command("list")
def list_histories_command() -> None:
    """List all histories in Galaxy."""
    # Initialize dependencies
    deps = init_dependencies()

    # Run get_histories tool using the helper function
    run_agent_command("List all histories", deps, "Error listing histories")


@history_app.command("create")
def create_history_command(name: str = typer.Argument(..., help="History name")) -> None:
    """Create a new history."""
    # Initialize dependencies
    deps = init_dependencies()

    # Run create_history tool using the helper function
    run_agent_command(f"Create a new history named: {name}", deps, "Error creating history")


@history_app.command("details")
def history_details_command(
    history_id: str = typer.Argument(..., help="History ID"),
) -> None:
    """Get detailed information about a specific history."""
    # Initialize dependencies
    deps = init_dependencies()

    # Run get_history_details tool using the helper function
    run_agent_command(
        f"Get details for history: {history_id}", deps, "Error retrieving history details"
    )


@workflow_app.command("list")
def list_workflows_command() -> None:
    """List all workflows from IWC."""
    # Initialize dependencies
    deps = init_dependencies()

    # Run get_iwc_workflows tool using the helper function
    run_agent_command("List all workflows from IWC", deps, "Error listing workflows")


@workflow_app.command("search")
def search_workflows_command(query: str = typer.Argument(..., help="Search query")) -> None:
    """Search for workflows in IWC."""
    # Initialize dependencies
    deps = init_dependencies()

    # Run search_iwc_workflows tool using the helper function
    run_agent_command(f"Search for workflows matching: {query}", deps, "Error searching workflows")


@workflow_app.command("import")
def import_workflow_command(
    trs_id: str = typer.Argument(..., help="TRS ID of the workflow"),
) -> None:
    """Import a workflow from IWC to Galaxy."""
    # Initialize dependencies
    deps = init_dependencies()

    # Run import_workflow_from_iwc tool using the helper function
    run_agent_command(f"Import workflow with TRS ID: {trs_id}", deps, "Error importing workflow")


@file_app.command("upload")
def upload_file_command(
    path: str = typer.Argument(..., help="Path to local file"),
    history_id: str = typer.Option(None, "--history", "-h", help="Target history ID"),
) -> None:
    """Upload a file to Galaxy."""
    # Initialize dependencies
    deps = init_dependencies()

    # Run upload_file tool using the helper function
    run_agent_command(
        f"Upload file: {path} to history: {history_id or 'default history'}",
        deps,
        "Error uploading file",
    )


@methods_app.command("generate")
def generate_methods_command(
    history_id: str = typer.Argument(..., help="History ID"),
) -> None:
    """Generate a methods section based on tools used in a history."""
    # Initialize dependencies
    deps = init_dependencies()

    # Show progress message
    console.print(
        "Generating methods section from history... This may take a moment.", style="yellow"
    )

    # Run generate_methods_section tool using the helper function
    run_agent_command(
        f"Generate methods section for history: {history_id}",
        deps,
        "Error generating methods section",
    )


async def run_interactive_command_async(user_input: str, deps: GalaxyDependencies) -> None:
    """Run a command in interactive mode asynchronously."""
    try:
        # Try to run with MCP servers
        try:
            # Run MCP servers inside an async context manager
            async with galaxy_agent.run_mcp_servers():
                response = await galaxy_agent.run(user_input, deps=deps)
                return response.output
        except Exception as mcp_error:
            # Check if it's the "Method not found" error for set_logging_level
            error_str = str(mcp_error)
            if "Method not found" in error_str:
                console.print("Warning: MCP server doesn't support certain methods. Falling back to direct agent use.", style="yellow")
                # Fall back to running the agent without the MCP context manager
                response = await galaxy_agent.run(user_input, deps=deps)
                return response.output
            else:
                # Re-raise other errors
                raise
    except Exception as e:
        console.print(f"Error processing request: {str(e)}", style="red")
        import traceback
        console.print(traceback.format_exc(), style="dim")
        return None

def run_interactive_command(user_input: str, deps: GalaxyDependencies, loop) -> None:
    """Run a command in interactive mode with the provided event loop."""
    try:
        # Use the same event loop for all commands, but with the proper async context
        response = loop.run_until_complete(run_interactive_command_async(user_input, deps))
        if response:
            handle_response(response)
    except Exception as e:
        console.print(f"Error processing request: {str(e)}", style="red")
        import traceback
        console.print(traceback.format_exc(), style="dim")


@app.command("test-mcp")
def test_mcp_command() -> None:
    """Test MCP server connection."""
    console.print("Testing MCP server connection...", style="yellow")
    console.print(f"MCP_SERVER_BASE_URL: {MCP_SERVER_BASE_URL}", style="blue")
    
    # First, check if we can access the mcp_servers property directly
    try:
        console.print(f"Agent: {galaxy_agent}", style="blue")
        mcp_servers = getattr(galaxy_agent, 'mcp_servers', None)
        console.print(f"MCP servers attribute found: {mcp_servers is not None}", style="blue")
        
        if mcp_servers is not None:
            console.print(f"MCP servers type: {type(mcp_servers)}", style="blue")
            console.print(f"MCP servers contents: {mcp_servers}", style="blue")
            console.print(f"MCP servers count: {len(mcp_servers) if hasattr(mcp_servers, '__len__') else 'Not a collection'}", style="blue")
        else:
            console.print("The agent does not have mcp_servers attribute set", style="yellow")
    except Exception as e:
        console.print(f"Error accessing mcp_servers attribute: {str(e)}", style="red")
    
    # Check if we can see any servers from our internal list 
    from galaxy_cli_agent.agent import mcp_server, mcp_servers_list
    console.print(f"Original MCP server: {mcp_server}", style="blue")
    console.print(f"Original MCP servers list: {mcp_servers_list}", style="blue")
    
    # Create an event loop for testing
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    # Check connection using an async context manager
    async def test_connection():
        try:
            console.print("Attempting to connect to MCP server via context manager...", style="blue")
            
            # Check if run_mcp_servers is available
            if not hasattr(galaxy_agent, 'run_mcp_servers'):
                console.print("❌ Agent does not have run_mcp_servers method", style="red")
                return False
            
            # Try using the run_mcp_servers approach
            try:
                console.print("Starting galaxy_agent.run_mcp_servers() context...", style="blue")
                
                # Directly print the method to inspect it
                console.print(f"run_mcp_servers method: {galaxy_agent.run_mcp_servers}", style="blue")
                
                # Check for the specific "Method not found" error related to set_logging_level
                try:
                    async with galaxy_agent.run_mcp_servers():
                        console.print("✅ MCP servers started successfully", style="green")
                        
                        # Try to test MCP communication
                        try:
                            console.print("Executing a simple test command via MCP...", style="blue")
                            # Create a simple test prompt
                            response = await galaxy_agent.run("What is the current time?")
                            console.print(f"✅ MCP connection working! Response received: {response}", style="green")
                            return True
                        except Exception as e:
                            console.print(f"❌ MCP communication failed: {str(e)}", style="red")
                            import traceback
                            console.print(traceback.format_exc(), style="dim")
                except Exception as e:
                    error_str = str(e)
                    if "Method not found" in error_str and "set_logging_level" in error_str:
                        console.print("⚠️ Found 'Method not found' error related to logging levels", style="yellow")
                        console.print("This is likely because the FastMCP server doesn't implement the set_logging_level method", style="yellow")
                        console.print("The MCP server connection might still be usable for basic operations", style="yellow")
                        
                        # Try to manually test the MCP server with a direct connection
                        try:
                            from mcp import ClientSession
                            from galaxy_cli_agent.agent import MCP_SERVER_BASE_URL
                            
                            # Extract the base URL
                            base_url = MCP_SERVER_BASE_URL.split("/sse")[0] if "/sse" in MCP_SERVER_BASE_URL else MCP_SERVER_BASE_URL
                            
                            # Try to connect directly to the MCP server (bypassing pydantic-ai)
                            console.print(f"Trying direct connection to MCP server at {base_url}/sse...", style="blue")
                            import httpx
                            async with httpx.AsyncClient() as client:
                                response = await client.get(f"{base_url}/sse")
                                console.print(f"Direct HTTP connection status: {response.status_code}", style="blue")
                                if response.status_code == 200:
                                    console.print("✅ MCP server is running and accessible via HTTP", style="green")
                                    return True
                        except Exception as direct_e:
                            console.print(f"⚠️ Direct connection test failed: {str(direct_e)}", style="yellow")
                    else:
                        console.print(f"❌ Failed to run MCP servers via context manager: {str(e)}", style="red")
                        import traceback
                        console.print(traceback.format_exc(), style="dim")
            except Exception as e:
                console.print(f"❌ Failed to run MCP servers via context manager: {str(e)}", style="red")
                import traceback
                console.print(traceback.format_exc(), style="dim")
        
        except Exception as e:
            console.print(f"❌ Overall MCP connection test failed: {str(e)}", style="red")
            import traceback
            console.print(traceback.format_exc(), style="dim")
        
        return False
    
    success = loop.run_until_complete(test_connection())
    loop.close()
    
    if not success:
        console.print("\nTroubleshooting tips:", style="yellow")
        console.print("1. Make sure the MCP server is running in another terminal", style="yellow")
        console.print(f"2. Check the server URL and port (currently using {MCP_SERVER_BASE_URL})", style="yellow")
        console.print("3. Try upgrading pydantic-ai to the latest version:", style="yellow")
        console.print("   pip install --upgrade pydantic-ai", style="yellow")
        console.print("4. Try different URL paths like /mcp or /sse depending on server transport", style="yellow")
        console.print("5. Check for any firewall or network issues blocking the connection", style="yellow")


@app.command("interact")
def interact_command() -> None:
    """Start interactive mode with natural language interface."""
    # Initialize dependencies
    deps = init_dependencies()

    console.print(
        Panel(
            "Starting interactive mode. Type 'exit' to quit.\n"
            "Type 'help' to see available commands.",
            title="Galaxy Agent Interactive Mode",
            style="blue",
        )
    )

    # Create a single event loop for the entire interactive session
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        # Print startup message about MCP server
        if hasattr(galaxy_agent, 'mcp_servers') and galaxy_agent.mcp_servers:
            console.print(
                f"MCP server connected at {MCP_SERVER_BASE_URL}. Natural language capabilities enhanced!", style="green"
            )
        else:
            console.print(
                "MCP server not connected. Natural language capabilities may be limited.", style="yellow"
            )
            
        # Try to auto-connect to Galaxy using environment variables
        console.print(
            "Attempting to connect to Galaxy using environment variables...", style="yellow"
        )
        run_interactive_command("connect", deps, loop)

        # Register signal handler for CTRL+C
        import signal

        def signal_handler(sig, frame):
            console.print("\nExiting Galaxy Agent. Goodbye!", style="green")
            loop.close()
            import sys

            sys.exit(0)

        # Register the signal handler
        signal.signal(signal.SIGINT, signal_handler)

        while True:
            try:
                # Get user input with proper rich formatting
                console.print("\n[bold cyan]Galaxy Agent>[/]", end="")
                user_input = input(" ")

                # Check for exit command
                if user_input.lower() in ("exit", "quit", "bye"):
                    console.print("Goodbye!", style="green")
                    break

                # Check for help command
                if user_input.lower() == "help":
                    help_text = f"""
                    Available commands:
                    - connect: Connect to Galaxy server
                    - search tools <query>: Search for Galaxy tools
                    - list histories: Get a list of your histories
                    - create history <name>: Create a new history
                    - search workflows <query>: Search for workflows in IWC
                    - generate methods <history_id>: Generate methods section
                    - help: Show this help message
                    - exit/quit/bye: Exit the program
                    - Ctrl+C: Exit the program
                    
                    MCP Server Status: {"Connected to " + MCP_SERVER_BASE_URL if hasattr(galaxy_agent, 'mcp_servers') and galaxy_agent.mcp_servers else "Not connected"}
                    
                    You can use natural language to interact with Galaxy!
                    Examples:
                    - "Find tools for RNA-seq analysis"
                    - "Create a new history called my experiment"
                    - "Show me tools that work with VCF files"
                    - "What workflows are available for bacterial genome assembly?"
                    - "I need to analyze ChIP-seq data from human samples"
                    """
                    console.print(Panel(help_text, title="Help", style="blue"))
                    continue

                # Run agent with user input
                console.print("Processing...", style="yellow")
                run_interactive_command(user_input, deps, loop)

            except KeyboardInterrupt:
                # This should now be handled by the signal handler
                # but keep as a fallback
                console.print("\nExiting Galaxy Agent. Goodbye!", style="green")
                break
            except Exception as e:
                console.print(f"Error: {str(e)}", style="red")
    finally:
        # Close the event loop when exiting
        loop.close()


if __name__ == "__main__":
    app()
