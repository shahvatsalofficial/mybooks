"""
Recipe 06.5: Pytest Integration Test Suite for FastMCP Server
Author: Vatsal Shah (Opportunity4u Press)
License: Apache-2.0
"""

import pytest
import json
from mcp.server.fastmcp import FastMCP
from pydantic import ValidationError

@pytest.fixture
def test_mcp_server():
    server = FastMCP("test-risk-server")

    @server.tool()
    def calculate_margin(exposure_usd: float, leverage: int = 1) -> float:
        """Calculates margin requirements."""
        if leverage <= 0:
            raise ValueError("Leverage must be greater than 0")
        return exposure_usd / leverage

    return server

def test_tool_registration(test_mcp_server):
    """Verifies tool reflection and metadata extraction."""
    tools = test_mcp_server._tool_manager.list_tools()
    tool_names = [t.name for t in tools]
    assert "calculate_margin" in tool_names
    
    target_tool = next(t for t in tools if t.name == "calculate_margin")
    assert target_tool.description == "Calculates margin requirements."
    assert "exposure_usd" in target_tool.inputSchema["properties"]
    assert "leverage" in target_tool.inputSchema["properties"]

@pytest.mark.asyncio
async def test_tool_execution_success(test_mcp_server):
    """Tests asynchronous execution of registered tool."""
    result = await test_mcp_server.call_tool("calculate_margin", {"exposure_usd": 10000.0, "leverage": 5})
    assert len(result) > 0
    assert float(result[0].text) == 2000.0

@pytest.mark.asyncio
async def test_tool_validation_failure(test_mcp_server):
    """Verifies that invalid parameter types raise validation errors."""
    with pytest.raises(Exception):
        # String passed to float field
        await test_mcp_server.call_tool("calculate_margin", {"exposure_usd": "one_million"})
