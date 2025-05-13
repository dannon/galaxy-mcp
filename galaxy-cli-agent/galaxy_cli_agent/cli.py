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
from rich.markdown import Markdown

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
methods_app = typer.Typer(help="Methods and citations operations")

app.add_typer(tools_app, name="tools")
app.add_typer(workflow_app, name="workflow")
app.add_typer(history_app, name="history")
app.add_typer(file_app, name="file")
app.add_typer(methods_app, name="methods")


# Helper function to load environment variables
def load_env_vars() -> tuple[Optional[str], Optional[str], Optional[str]]:
    """Load Galaxy URL, API key, and Google API key from environment variables or .env file."""
    # Try to load environment variables from .env file
    dotenv_path = find_dotenv(usecwd=True)
    if dotenv_path:
        load_dotenv(dotenv_path)

    return (
        os.environ.get("GALAXY_URL"),
        os.environ.get("GALAXY_API_KEY"),
        os.environ.get("GOOGLE_API_KEY"),
    )


# Helper function to initialize Galaxy dependencies
def init_dependencies() -> GalaxyDependencies:
    """Initialize Galaxy dependencies from environment variables or .env file."""
    galaxy_url, api_key, google_api_key = load_env_vars()

    # Set the Google API key for Gemini
    if google_api_key:
        os.environ["GOOGLE_API_KEY"] = google_api_key
    else:
        console.print(
            "Warning: GOOGLE_API_KEY not found in environment variables or .env file. "
            "This is required for the Gemini model to function.",
            style="yellow",
        )

    deps = GalaxyDependencies(
        galaxy_url=galaxy_url,
        api_key=api_key,
        connected=False,
    )

    return deps


# Helper function to run agent commands
def run_agent_command(prompt: str, deps: GalaxyDependencies, error_prefix: str = "Error") -> None:
    """Run an agent command with standardized error handling."""
    try:
        response = asyncio.run(galaxy_agent.run(prompt, deps=deps))
        # The agent.run() returns an AgentRunResult object which has an 'output' attribute
        # that contains the actual GalaxyResponse
        handle_response(response.output)
    except Exception as e:
        console.print(f"{error_prefix}: {str(e)}", style="red")
        import traceback

        console.print(traceback.format_exc(), style="dim")


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
        console.print(Panel(response.message, title="Error", style="red"))


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


def run_interactive_command(user_input: str, deps: GalaxyDependencies, loop) -> None:
    """Run a command in interactive mode with the provided event loop."""
    try:
        # Use the same event loop for all commands
        response = loop.run_until_complete(galaxy_agent.run(user_input, deps=deps))
        handle_response(response.output)
    except Exception as e:
        console.print(f"Error processing request: {str(e)}", style="red")
        import traceback

        console.print(traceback.format_exc(), style="dim")


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
                    help_text = """
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
                    
                    You can also use natural language to ask about Galaxy!
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
