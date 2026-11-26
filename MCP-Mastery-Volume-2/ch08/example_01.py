"""
tests/conftest.py - Production In-Memory MCP Test Fixture
Provides isolated, sub-millisecond client harnesses for Pytest suites.
"""

import asyncio
from typing import AsyncGenerator
import pytest
import pytest_asyncio
from mcp import ClientSession
from mcp.server.fastmcp import FastMCP
from mcp.shared.memory import create_in_memory_transport

# Example Production Server Under Test
server = FastMCP("EnterpriseInventoryServer")

@server.tool()
async def check_inventory(sku: str, warehouse_id: str) -> dict:
    """Check physical inventory levels for a given SKU and warehouse."""
    if not sku.startswith("SKU-"):
        raise ValueError("Invalid SKU format. Must start with 'SKU-'.")
    if warehouse_id not in ["WH-NORTH", "WH-SOUTH", "WH-EAST"]:
        raise ValueError(f"Unknown warehouse identifier: {warehouse_id}")
    
    # Deterministic mock business logic
    return {
        "sku": sku,
        "warehouse_id": warehouse_id,
        "available_units": 142,
        "reserved_units": 8,
        "reorder_threshold": 50,
        "status": "IN_STOCK"
    }

@server.resource("inventory://metrics/{warehouse_id}")
async def warehouse_metrics(warehouse_id: str) -> str:
    """Retrieve operational metrics for an inventory warehouse."""
    if warehouse_id not in ["WH-NORTH", "WH-SOUTH", "WH-EAST"]:
        raise ValueError(f"Warehouse {warehouse_id} not found.")
    return f"Status: OPERATIONAL | Capacity: 88% | Active Workers: 24 | Temp: 4.2C"


@pytest_asyncio.fixture
async def mcp_client() -> AsyncGenerator[ClientSession, None]:
    """
    Spawns an in-process, bidirectional in-memory client-server harness.
    Completely avoids OS subprocess overhead and TCP port bindings.
    """
    # Create linked in-memory streams
    client_read, server_write = create_in_memory_transport()
    server_read, client_write = create_in_memory_transport()

    # Launch server message pump as a concurrent background task
    server_task = asyncio.create_task(
        server._mcp_server.run(
            server_read,
            server_write,
            server._mcp_server.create_initialization_options()
        )
    )

    # Instantiate and initialize the client session
    async with ClientSession(client_read, client_write) as session:
        # Perform standard MCP protocol initialization handshake
        init_result = await session.initialize()
        assert init_result.protocolVersion is not None
        assert "tools" in init_result.capabilities
        assert "resources" in init_result.capabilities

        yield session

    # Graceful shutdown: cancel server background pump
    server_task.cancel()
    try:
        await server_task
    except asyncio.CancelledError:
        pass
