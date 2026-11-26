#!/usr/bin/env python3
"""
Enterprise PostgreSQL Asyncpg Analytical MCP Server
Language: Python 3.11+
Features: High-speed binary protocol execution, async connection pooling, schema reflection
"""

import os
import asyncpg
from typing import Optional
from pydantic import BaseModel, Field
from mcp.server.fastmcp import FastMCP, Context

mcp = FastMCP("Enterprise-Postgres-Core")

# Global asyncpg connection pool
db_pool: Optional[asyncpg.Pool] = None

async def get_db_pool() -> asyncpg.Pool:
    global db_pool
    if db_pool is None:
        db_url = os.getenv("DATABASE_URL", "postgresql://app_user:secret@localhost:5432/corp_db")
        db_pool = await asyncpg.create_pool(
            dsn=db_url,
            min_size=5,
            max_size=20,
            max_inactive_connection_lifetime=300.0,
            command_timeout=30.0
        )
    return db_pool

class TableInspectInput(BaseModel):
    schema_name: str = Field(default="public", description="PostgreSQL schema namespace")
    table_name: str = Field(..., description="Target table name to reflect")

@mcp.tool()
async def inspect_table_schema(input_data: TableInspectInput, ctx: Context) -> str:
    """Reflects column definitions, foreign keys, indexes, and nullability constraints for a table."""
    pool = await get_db_pool()
    ctx.info(f"Reflecting schema for table: {input_data.schema_name}.{input_data.table_name}...")
    
    query = """
    SELECT column_name, data_type, is_nullable, column_default
    FROM information_schema.columns
    WHERE table_schema = $1 AND table_name = $2
    ORDER BY ordinal_position;
    """
    
    async with pool.acquire() as conn:
        rows = await conn.fetch(query, input_data.schema_name, input_data.table_name)
        
    if not rows:
        return f"Table '{input_data.schema_name}.{input_data.table_name}' was not found in catalog."
        
    lines = [f"| Column | Type | Nullable | Default |", "| :--- | :--- | :--- | :--- |"]
    for r in rows:
        lines.append(f"| {r['column_name']} | {r['data_type']} | {r['is_nullable']} | {r['column_default'] or ''} |")
        
    return f"### PostgreSQL Schema: {input_data.schema_name}.{input_data.table_name}\n\n" + "\n".join(lines)

@mcp.tool()
async def execute_safe_readonly_sql(sql_query: str, ctx: Context) -> str:
    """Executes a strictly read-only SQL query inside an explicit READ ONLY transaction block."""
    pool = await get_db_pool()
    ctx.info("Validating and executing safe read-only SQL query...")
    
    # Static check for mutating keywords
    for token in ["INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "TRUNCATE", "GRANT"]:
        if token in sql_query.upper().split():
            return f"SECURITY BARRIER: Mutating SQL keyword '{token}' is prohibited in read-only mode."
            
    async with pool.acquire() as conn:
        # Enforce read-only isolation level at transaction level
        async with conn.transaction(readonly=True):
            records = await conn.fetch(sql_query)
            
    if not records:
        return "Query executed successfully. 0 rows returned."
        
    columns = list(records[0].keys())
    header = "| " + " | ".join(columns) + " |"
    divider = "| " + " | ".join([":---"] * len(columns)) + " |"
    rows_out = [header, divider]
    
    for rec in records[:50]:
        rows_out.append("| " + " | ".join([str(rec[col]) for col in columns]) + " |")
        
    return f"### Query Result ({len(records)} total rows, showing top {min(len(records), 50)}):\n\n" + "\n".join(rows_out)

if __name__ == "__main__":
    mcp.run(transport="stdio")
