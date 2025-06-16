"""Tests for the CLI interface."""

from unittest.mock import AsyncMock, Mock, patch

import pytest
from typer.testing import CliRunner

from galaxy_cli_agent.agent import GalaxyResponse
from galaxy_cli_agent.cli import app, handle_response, init_dependencies


class TestCLIFunctions:
    """Test CLI helper functions."""

    def test_init_dependencies(self):
        """Test dependency initialization."""
        deps = init_dependencies()
        assert deps is not None

    def test_handle_response_success(self, capsys):
        """Test handling successful response."""
        response = GalaxyResponse(
            success=True, message="Test success message", operation="test_op", data={"key": "value"}
        )

        with patch("galaxy_cli_agent.cli.console") as mock_console:
            handle_response(response)
            # Verify console.print was called for success
            assert mock_console.print.called

    def test_handle_response_failure(self):
        """Test handling failed response."""
        response = GalaxyResponse(success=False, message="Test error message", operation="test_op")

        with patch("galaxy_cli_agent.cli.console") as mock_console:
            handle_response(response)
            # Verify console.print was called for error
            assert mock_console.print.called


class TestCLICommands:
    """Test CLI command structure."""

    def test_cli_app_structure(self):
        """Test that CLI app has expected subcommands."""
        runner = CliRunner()
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "tools" in result.output
        assert "workflow" in result.output
        assert "history" in result.output
        assert "file" in result.output
        assert "methods" in result.output

    @pytest.mark.asyncio
    async def test_run_agent_command_async_mock(self):
        """Test the async agent command runner with mocked agent."""
        from galaxy_cli_agent.agent import create_dependencies
        from galaxy_cli_agent.cli import run_agent_command_async

        deps = create_dependencies()

        # Mock the galaxy_agent.run method
        mock_result = Mock()
        mock_result.output = GalaxyResponse(
            success=True, message="Mocked response", operation="test"
        )

        # Create a proper async context manager mock
        mock_context_manager = AsyncMock()
        mock_context_manager.__aenter__ = AsyncMock(return_value=None)
        mock_context_manager.__aexit__ = AsyncMock(return_value=None)

        with patch("galaxy_cli_agent.cli.galaxy_agent") as mock_agent:
            mock_agent.run_mcp_servers.return_value = mock_context_manager
            mock_agent.run = AsyncMock(return_value=mock_result)

            # Test the function
            result = await run_agent_command_async("test prompt", deps, "Test Error")

            assert result is not None
            assert isinstance(result, GalaxyResponse)
            assert result.success is True
