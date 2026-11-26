import pytest
from mcp.server.fastmcp import FastMCP

@pytest.mark.asyncio
async def test_duckdb_tool_execution():
    mcp = FastMCP("TestServer")
    
    @mcp.tool()
    def add_numbers(a: int, b: int) -> int:
        return a + b
        
    # Execute tool directly through internal FastMCP dispatcher
    result = await mcp.call_tool("add_numbers", {"a": 40, "b": 2})
    assert result == 42

@pytest.mark.asyncio
async def test_schema_validation_rejection():
    mcp = FastMCP("TestServer")
    
    @mcp.tool()
    def process_age(age: int) -> str:
        return f"Age: {age}"
        
    with pytest.raises(Exception):
        # Passing invalid string type where integer is required
        await mcp.call_tool("process_age", {"age": "not-an-integer"})
