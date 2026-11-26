"""
Enterprise PostgreSQL MCP Bridge with SQLGlot AST Sanitization & Context Budget Guards
Author: Vatsal Shah | Opportunity4u Press
Runtime: Python 3.11+ with FastMCP, SQLGlot & asyncpg
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional
import asyncpg
import sqlglot
from sqlglot import exp
from pydantic import BaseModel, Field
from mcp.server.fastmcp import FastMCP, Context
from mcp.shared.exceptions import McpError
from mcp.types import ErrorCode

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("mcp.db.postgres")

class SqlQuerySanitizer:
    """Enforces AST-level read-only guarantees and row limit clamping."""

    MAX_PERMITTED_ROWS = 500

    @classmethod
    def sanitize_and_clamp_query(cls, raw_sql: str) -> str:
        """Parse SQL string into AST, assert single SELECT, and clamp LIMIT."""
        try:
            # Parse SQL statements using PostgreSQL dialect
            statements = sqlglot.parse(raw_sql, read="postgres")
        except Exception as pe:
            raise McpError(ErrorCode.InvalidParams, f"SQL Syntax Error: Unable to parse query: {str(pe)}")

        if not statements or len(statements) == 0:
            raise McpError(ErrorCode.InvalidParams, "Empty SQL query submitted")

        if len(statements) > 1:
            raise McpError(
                ErrorCode.InvalidParams,
                f"Security Violation: Multi-statement batch queries are prohibited. "
                f"Detected {len(statements)} statements."
            )

        stmt = statements[0]

        # Enforce Root Node must be SELECT
        if not isinstance(stmt, exp.Select):
            raise McpError(
                ErrorCode.InvalidParams,
                f"Security Violation: Only SELECT queries are permitted on this bridge. "
                f"Attempted execution of: {type(stmt).__name__.upper()}"
            )

        # Inspect AST recursively for forbidden DDL / DML nodes
        forbidden_types = (
            exp.Drop, exp.Alter, exp.Insert, exp.Update, exp.Delete,
            exp.Create, exp.Truncate, exp.Merge, exp.Command
        )
        for node in stmt.walk():
            if isinstance(node, forbidden_types):
                raise McpError(
                    ErrorCode.InvalidParams,
                    f"Security Violation: Forbidden expression '{type(node).__name__}' detected in query tree"
                )

        # Enforce and Clamp LIMIT clause
        limit_node = stmt.find(exp.Limit)
        if limit_node:
            try:
                current_limit = int(limit_node.expression.this)
                if current_limit > cls.MAX_PERMITTED_ROWS or current_limit <= 0:
                    logger.info(f"Clamping user limit {current_limit} to {cls.MAX_PERMITTED_ROWS}")
                    stmt.set("limit", exp.Limit(expression=exp.Literal.number(cls.MAX_PERMITTED_ROWS)))
            except (ValueError, AttributeError):
                stmt.set("limit", exp.Limit(expression=exp.Literal.number(cls.MAX_PERMITTED_ROWS)))
        else:
            # Inject mandatory LIMIT 500
            stmt.set("limit", exp.Limit(expression=exp.Literal.number(cls.MAX_PERMITTED_ROWS)))

        return stmt.sql(dialect="postgres")


class PostgresDatabaseBridge:
    """Async connection pool manager with read-only transaction configuration."""

    def __init__(self, dsn: str, max_connections: int = 15):
        self.dsn = dsn
        self.max_connections = max_connections
        self._pool: Optional[asyncpg.Pool] = None

    async def initialize(self):
        logger.info("Initializing asyncpg connection pool...")
        self._pool = await asyncpg.create_pool(
            dsn=self.dsn,
            min_size=2,
            max_size=self.max_connections,
            command_timeout=5.0,
            server_settings={
                "statement_timeout": "3000ms",
                "idle_in_transaction_session_timeout": "4000ms",
                "default_transaction_read_only": "on"
            }
        )

    async def execute_query(self, sanitized_sql: str) -> List[Dict[str, Any]]:
        if not self._pool:
            raise RuntimeError("Database bridge pool not initialized")

        async with self._pool.acquire() as conn:
            async with conn.transaction(readonly=True):
                records = await conn.fetch(sanitized_sql)
                return [dict(r) for r in records]

    async def close(self):
        if self._pool:
            await self._pool.close()


# Initialize Components
db_bridge = PostgresDatabaseBridge(
    dsn=os.getenv("DATABASE_URL", "postgresql://readonly_agent:secure_pass@localhost:5432/analytics_db")
)
mcp = FastMCP("Enterprise-PostgreSQL-Bridge")


class ExecuteQueryInput(BaseModel):
    query: str = Field(description="Standard PostgreSQL SELECT query to execute against analytical warehouse")


@mcp.tool(description="Execute sanitized read-only SQL query against enterprise PostgreSQL replica")
async def execute_sql_query(params: ExecuteQueryInput, ctx: Context) -> str:
    """Safe analytical query tool with AST sanitization and context truncation."""
    raw_query = params.query.strip()
    logger.info(f"Incoming raw query: {raw_query}")

    # 1. AST Sanitization and Limit Clamping
    sanitized_sql = SqlQuerySanitizer.sanitize_and_clamp_query(raw_query)
    logger.info(f"Sanitized query: {sanitized_sql}")

    # 2. Database Execution
    try:
        results = await db_bridge.execute_query(sanitized_sql)
    except asyncpg.PostgresError as pe:
        logger.error(f"PostgreSQL Execution Error: {str(pe)}")
        raise McpError(ErrorCode.InternalError, f"Database error during query execution: {str(pe)}")

    # 3. Context Budget Guard & Output Serialization
    serialized = json.dumps(results, default=str)
    char_count = len(serialized)
    row_count = len(results)

    # 25,000 Character Context Window Ceiling
    if char_count > 25000:
        logger.warning(f"Payload exceeded budget ({char_count} chars). Applying graceful truncation.")
        truncated_rows = results[:25]
        return json.dumps({
            "status": "partial_success",
            "warning": "Result truncated: Total data exceeds context budget. Showing first 25 rows.",
            "total_rows_returned": row_count,
            "total_characters_raw": char_count,
            "sample_data": truncated_rows
        }, default=str)

    return serialized
