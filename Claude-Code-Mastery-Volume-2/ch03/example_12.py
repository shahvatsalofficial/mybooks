#!/usr/bin/env python3
"""
Enterprise Analytical DuckDB MCP Server
Language: Python 3.11+
Framework: FastMCP
Target: High-speed local analytical queries over Parquet data lakes
"""

import sys
import os
import duckdb
from typing import Optional
from pydantic import BaseModel, Field
from mcp.server.fastmcp import FastMCP, Context

mcp = FastMCP("Enterprise-DuckDB-Analytics")

DUCKDB_PATH = os.getenv("DUCKDB_DATABASE_PATH", ":memory:")
con = duckdb.connect(DUCKDB_PATH)
con.execute("SET memory_limit = '4GB';")
con.execute("SET threads TO 4;")

class SqlQueryInput(BaseModel):
    query: str = Field(
        ...,
        description="The SQL query to execute. Can query tables, Parquet files directly via read_parquet(), or CSVs."
    )
    max_rows: int = Field(
        default=50,
        ge=1,
        le=500,
        description="Maximum number of rows to return in the JSON result payload (capped at 500)"
    )

@mcp.tool()
async def execute_analytical_sql(input_data: SqlQueryInput, ctx: Context) -> str:
    """Executes a high-performance OLAP query using DuckDB. Supports direct querying of Parquet/CSV files."""
    cleaned_query = input_data.query.strip()
    ctx.info(f"Executing DuckDB analytical query: {cleaned_query[:80]}...")
    
    # Safety Barrier: Restrict destructive operations on persistent catalogs
    prohibited = ["DROP", "DELETE", "TRUNCATE", "ALTER", "ATTACH"]
    for keyword in prohibited:
        if keyword in cleaned_query.upper().split():
            return f"SECURITY VIOLATION: Statement contains prohibited administrative keyword '{keyword}'."
            
    try:
        result_df = con.execute(cleaned_query).fetch_df()
        row_count = len(result_df)
        
        truncated_df = result_df.head(input_data.max_rows)
        markdown_table = truncated_df.to_markdown(index=False)
        
        summary_header = f"### Query Result ({row_count} total rows returned, showing top {len(truncated_df)}):

"
        return summary_header + markdown_table
    except Exception as err:
        ctx.error(f"DuckDB Query execution failed: {err}")
        return f"DUCKDB SQL ERROR: {str(err)}"

class ParquetInspectInput(BaseModel):
    file_path: str = Field(
        ...,
        description="Path to local or remote Parquet file (e.g. data/sales_2026.parquet or s3://bucket/data.parquet)"
    )

@mcp.tool()
async def inspect_parquet_schema(input_data: ParquetInspectInput) -> str:
    """Extracts column data types, row counts, and compression metadata from a Parquet dataset."""
    try:
        query = f"DESCRIBE SELECT * FROM read_parquet('{input_data.file_path}') LIMIT 1;"
        schema_df = con.execute(query).fetch_df()
        
        count_query = f"SELECT count(*) as total_rows FROM read_parquet('{input_data.file_path}');"
        total_rows = con.execute(count_query).fetchone()[0]
        
        return f"### Parquet Dataset Metadata for: {input_data.file_path}
" \
               f"**Total Record Count:** {total_rows:,}

" \
               f"**Schema Definition:**
" + schema_df.to_markdown(index=False)
    except Exception as err:
        return f"PARQUET INSPECTION FAILED: {str(err)}"

@mcp.resource("duckdb://summary/{table_name}")
def get_table_summary(table_name: str) -> str:
    """Provides automated statistical percentiles, min, max, and null-counts for an active table."""
    try:
        query = f"SUMMARIZE {table_name};"
        summary_df = con.execute(query).fetch_df()
        return summary_df.to_markdown(index=False)
    except Exception as err:
        return f"FAILED TO GENERATE SUMMARY FOR {table_name}: {str(err)}"

if __name__ == "__main__":
    mcp.run(transport="stdio")
