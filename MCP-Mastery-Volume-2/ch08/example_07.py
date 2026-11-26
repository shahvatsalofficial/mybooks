"""
tests/test_enterprise_suite.py - Full Production MCP Verification Suite
Validates tools, resources, prompts, and error paths under Pytest.
"""

import asyncio
import json
import pytest
import pytest_asyncio
from typing import AsyncGenerator
from mcp import ClientSession
from mcp.server.fastmcp import FastMCP
from mcp.shared.memory import create_in_memory_transport
from mcp.types import TextContent, PromptMessage

# ---------------------------------------------------------
# Production Server Definition Under Test
# ---------------------------------------------------------
app = FastMCP("DataOpsServer")

@app.tool()
async def execute_query(sql: str, read_only: bool = True) -> str:
    """Execute a validated SQL query against the read-replica data warehouse."""
    normalized_sql = sql.strip().upper()
    
    # Enforce read-only constraint
    destructive_keywords = ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "TRUNCATE"]
    if read_only and any(keyword in normalized_sql for keyword in destructive_keywords):
        raise PermissionError("Destructive SQL commands are forbidden in read-only mode.")
    
    # Deterministic query result
    return json.dumps({
        "status": "SUCCESS",
        "rows_returned": 2,
        "columns": ["id", "username", "role"],
        "records": [
            [101, "vatsal_dev", "platform_admin"],
            [102, "claude_agent", "auditor"]
        ]
    })

@app.resource("schema://warehouse/{table_name}")
async def get_table_schema(table_name: str) -> str:
    """Provide schema DDL for requested analytical table."""
    valid_tables = ["users", "orders", "telemetry"]
    if table_name not in valid_tables:
        raise FileNotFoundError(f"Table '{table_name}' does not exist in schema registry.")
    
    return f"CREATE TABLE {table_name} (id BIGINT PRIMARY KEY, created_at TIMESTAMP NOT NULL);"

@app.prompt()
async def incident_investigation(incident_id: str) -> list[PromptMessage]:
    """Generate prompt context for investigating an enterprise production incident."""
    return [
        PromptMessage(
            role="user",
            content=TextContent(
                type="text",
                text=f"Begin forensic investigation for Incident #{incident_id}. "
                     f"Inspect system telemetry and audit database logs using available tools."
            )
        )
    ]

# ---------------------------------------------------------
# Test Harness & Fixtures
# ---------------------------------------------------------
@pytest_asyncio.fixture
async def client() -> AsyncGenerator[ClientSession, None]:
    """Instantiate in-memory client-server harness for sub-millisecond execution."""
    c_read, s_write = create_in_memory_transport()
    s_read, c_write = create_in_memory_transport()

    server_task = asyncio.create_task(
        app._mcp_server.run(
            s_read,
            s_write,
            app._mcp_server.create_initialization_options()
        )
    )

    async with ClientSession(c_read, c_write) as session:
        await session.initialize()
        yield session

    server_task.cancel()
    try:
        await server_task
    except asyncio.CancelledError:
        pass

# ---------------------------------------------------------
# Test Cases
# ---------------------------------------------------------
@pytest.mark.asyncio
async def test_execute_query_valid_select(client: ClientSession):
    """Test valid SELECT query execution and structured output decoding."""
    result = await client.call_tool(
        "execute_query",
        arguments={"sql": "SELECT id, username, role FROM users LIMIT 10;", "read_only": True}
    )

    assert result.isError is not True
    assert len(result.content) == 1
    
    data = json.loads(result.content[0].text)
    assert data["status"] == "SUCCESS"
    assert data["rows_returned"] == 2
    assert data["records"][0][1] == "vatsal_dev"


@pytest.mark.asyncio
async def test_execute_query_destructive_command_rejected(client: ClientSession):
    """Verify safety guard catches destructive commands in read-only mode."""
    result = await client.call_tool(
        "execute_query",
        arguments={"sql": "DROP TABLE users;", "read_only": True}
    )

    assert result.isError is True
    assert "Destructive SQL commands are forbidden" in result.content[0].text


@pytest.mark.asyncio
async def test_get_table_schema_resource_resolution(client: ClientSession):
    """Verify resource template dynamically resolves table schema definitions."""
    res = await client.read_resource("schema://warehouse/users")
    
    assert res is not None
    assert len(res.contents) == 1
    assert "CREATE TABLE users" in res.contents[0].text


@pytest.mark.asyncio
async def test_get_table_schema_missing_table_error(client: ClientSession):
    """Verify resource read fails gracefully for non-existent tables."""
    with pytest.raises(Exception) as excinfo:
        await client.read_resource("schema://warehouse/non_existent_table")
    
    assert "does not exist" in str(excinfo.value) or "error" in str(excinfo.value).lower()


@pytest.mark.asyncio
async def test_incident_investigation_prompt_expansion(client: ClientSession):
    """Verify prompt template expands into structured conversation messages."""
    prompt_result = await client.get_prompt(
        "incident_investigation",
        arguments={"incident_id": "INC-8802"}
    )

    assert prompt_result is not None
    assert len(prompt_result.messages) == 1
    msg = prompt_result.messages[0]
    assert msg.role == "user"
    assert "Incident #INC-8802" in msg.content.text
    assert "forensic investigation" in msg.content.text
