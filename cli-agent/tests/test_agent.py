"""Tests for the Galaxy CLI agent."""

from unittest.mock import Mock

import pytest

from galaxy_cli_agent.agent import (
    GalaxyDependencies,
    GalaxyResponse,
    create_dependencies,
    galaxy_agent,
)


class TestGalaxyAgent:
    """Test the Galaxy CLI agent functionality."""

    def test_create_dependencies(self):
        """Test that dependencies can be created."""
        deps = create_dependencies()
        assert isinstance(deps, GalaxyDependencies)
        assert isinstance(deps.mcp_available, bool)

    def test_galaxy_response_model(self):
        """Test the GalaxyResponse model."""
        response = GalaxyResponse(success=True, message="Test message", operation="test_operation")
        assert response.success is True
        assert response.message == "Test message"
        assert response.operation == "test_operation"
        assert response.data is None

    def test_galaxy_response_with_data(self):
        """Test GalaxyResponse with data."""
        test_data = {"key": "value"}
        response = GalaxyResponse(
            success=True, message="Test with data", operation="test_operation", data=test_data
        )
        assert response.data == test_data

    @pytest.mark.asyncio()
    async def test_generate_methods_section_placeholder(self):
        """Test the generate_methods_section tool (placeholder implementation)."""
        # Import the function directly to test it
        from galaxy_cli_agent.agent import generate_methods_section

        deps = create_dependencies()
        mock_ctx = Mock()
        mock_ctx.deps = deps

        # Test the placeholder implementation
        result = await generate_methods_section(mock_ctx, "test_history_123")

        assert isinstance(result, GalaxyResponse)
        assert result.success is True
        assert result.operation == "generate_methods_section"
        assert "pending_implementation" in result.data["status"]


class TestAgentIntegration:
    """Test agent integration with MCP servers."""

    @pytest.mark.asyncio()
    async def test_agent_can_be_initialized(self):
        """Test that the agent can be initialized."""
        assert galaxy_agent is not None
        # Check that the agent exists and has basic functionality
        # We don't need to check internal attributes - just that it works
        assert callable(galaxy_agent.run)

    def test_agent_has_mcp_servers(self):
        """Test that agent can be configured with MCP servers."""
        # This tests the configuration, not actual connection
        # since we don't want tests to depend on running MCP server
        assert hasattr(galaxy_agent, "_mcp_servers")
        # The actual MCP servers list depends on environment/configuration
