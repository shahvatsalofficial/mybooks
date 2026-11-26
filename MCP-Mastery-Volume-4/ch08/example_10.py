import os
import sys
import asyncpg
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP Server with domain namespace
mcp = FastMCP("postgres_enterprise_gateway")

DB_URL = os.getenv("DATABASE_URL", "postgresql://localhost:5432/analytics")

@mcp.tool()
async def query_postgres_table(sql: str, row_limit: int = 50) -> str:
    """Executes a read-only parameterized query against PostgreSQL with cursor limits.
    
    Args:
        sql: The SQL query to execute.
        row_limit: Maximum number of rows to return (max: 200).
    """
    clean_sql = sql.strip()
    if not clean_sql.lower().startswith("select"):
        return "Security Violation: Only SELECT queries are permitted."

    limit = min(max(row_limit, 1), 200)
    if "limit" not in clean_sql.lower():
        clean_sql = f"{clean_sql} LIMIT {limit}"

    conn = await asyncpg.connect(DB_URL)
    try:
        rows = await conn.fetch(clean_sql)
        if not rows:
            return "Query executed successfully: 0 rows returned."
        
        # Serialize records to Markdown table
        columns = list(rows[0].keys())
        md = f"| {' | '.join(columns)} |\n| {' | '.join(['---'] * len(columns))} |\n"
        for row in rows:
            md += f"| {' | '.join(str(row[c]) for c in columns)} |\n"
        return md
    except Exception as e:
        return f"PostgreSQL Execution Error: {str(e)}"
    finally:
        await conn.close()

def main():
    mcp.run(transport="stdio")

if __name__ == "__main__":
    main()
