"""
Multi-Tenant FastMCP Server with Task-Scoped ContextVar & PostgreSQL Schema Isolation
Author: Vatsal Shah | Opportunity4u Press
Architecture: Async Context Propagation & Dynamic Schema Switching
"""

import os
import json
import logging
import asyncio
from typing import Dict, Any, Optional
from contextvars import ContextVar
import asyncpg
from pydantic import BaseModel, Field
from mcp.server.fastmcp import FastMCP, Context
from mcp.shared.exceptions import McpError
from mcp.types import ErrorCode

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("mcp.multitenant.server")

# 1. Thread-safe & Task-safe Context Storage
CURRENT_TENANT_ID: ContextVar[str] = ContextVar("CURRENT_TENANT_ID", default="unassigned")
CURRENT_USER_ID: ContextVar[str] = ContextVar("CURRENT_USER_ID", default="anonymous")

class TenantDatabaseRouter:
    """Manages pooled PostgreSQL connections with dynamic search_path schema scoping."""

    def __init__(self, dsn: str, min_size: int = 5, max_size: int = 20):
        self.dsn = dsn
        self.min_size = min_size
        self.max_size = max_size
        self._pool: Optional[asyncpg.Pool] = None

    async def initialize(self):
        """Initialize global connection pool."""
        logger.info("Initializing multi-tenant PostgreSQL connection pool...")
        self._pool = await asyncpg.create_pool(
            dsn=self.dsn,
            min_size=self.min_size,
            max_size=self.max_size,
            command_timeout=30.0
        )

    async def execute_in_tenant_schema(self, query: str, *args) -> list:
        """Execute query strictly within the active tenant's PostgreSQL schema."""
        if not self._pool:
            raise RuntimeError("Database pool not initialized")

        tenant_id = CURRENT_TENANT_ID.get()
        if tenant_id == "unassigned":
            raise McpError(ErrorCode.InternalError, "Database execution attempted without tenant context")

        # Sanitize tenant identifier to prevent SQL injection in schema switching
        safe_schema = "".join(c for c in tenant_id if c.isalnum() or c == "_").lower()
        schema_name = f"tenant_{safe_schema}"

        async with self._pool.acquire() as conn:
            async with conn.transaction():
                # Dynamically bind search_path to tenant schema; fallback to public only for base types
                await conn.execute(f"SET LOCAL search_path TO {schema_name}, public;")
                records = await conn.fetch(query, *args)
                return [dict(r) for r in records]

    async def close(self):
        if self._pool:
            await self._pool.close()


# Initialize Router & Server
db_router = TenantDatabaseRouter(
    dsn=os.getenv("DATABASE_URL", "postgresql://mcp_user:mcp_pass@localhost:5432/enterprise_db")
)
mcp = FastMCP("MultiTenant-Enterprise-Gateway")


def tenant_scoped():
    """Middleware decorator extracting tenant context from request headers before tool execution."""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            ctx: Optional[Context] = kwargs.get("ctx")
            if not ctx:
                raise McpError(ErrorCode.InternalError, "Tool invoked without execution context")

            # Extract tenant and user identifiers from request metadata
            meta = ctx.request_context.meta
            raw_tenant = meta.get("x-tenant-id") or meta.get("tenant_id")
            raw_user = meta.get("x-user-id") or meta.get("user_id", "agent_worker")

            if not raw_tenant:
                raise McpError(ErrorCode.InvalidRequest, "Missing mandatory 'X-Tenant-ID' request header")

            # Bind ContextVar for the duration of this specific task
            t_token = CURRENT_TENANT_ID.set(str(raw_tenant).strip())
            u_token = CURRENT_USER_ID.set(str(raw_user).strip())

            try:
                logger.info(f"Dispatching tool '{func.__name__}' for tenant '{CURRENT_TENANT_ID.get()}'")
                return await func(*args, **kwargs)
            finally:
                # Guarantee context cleanup even on unhandled exceptions
                CURRENT_TENANT_ID.reset(t_token)
                CURRENT_USER_ID.reset(u_token)
        return wrapper
    return decorator


class OrderQueryInput(BaseModel):
    status_filter: str = Field(default="COMPLETED", description="Filter orders by status: PENDING, COMPLETED, CANCELLED")
    limit: int = Field(default=10, ge=1, le=100, description="Maximum records to retrieve")


@mcp.tool(description="Retrieve recent enterprise customer purchase orders within tenant partition")
@tenant_scoped()
async def fetch_customer_orders(params: OrderQueryInput, ctx: Context) -> str:
    """Safe tenant-isolated order retrieval tool."""
    active_tenant = CURRENT_TENANT_ID.get()
    
    query = """
        SELECT order_id, customer_name, total_amount, currency, created_at
        FROM orders
        WHERE status = $1
        ORDER BY created_at DESC
        LIMIT $2;
    """
    
    try:
        results = await db_router.execute_in_tenant_schema(query, params.status_filter, params.limit)
        return json.dumps({
            "status": "success",
            "tenant_id": active_tenant,
            "count": len(results),
            "orders": results
        }, default=str)
    except asyncpg.PostgresError as pe:
        logger.error(f"PostgreSQL query failed for tenant '{active_tenant}': {str(pe)}")
        raise McpError(ErrorCode.InternalError, f"Failed to execute tenant query: {str(pe)}")
