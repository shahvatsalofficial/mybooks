"""
Recipe 07.1: Enterprise Hardened PostgreSQL MCP Server
Author: Vatsal Shah (Vatsal Shah)
License: Apache-2.0
"""

import os
import json
import logging
from typing import Dict, Any, List
import psycopg2
from psycopg2.extras import RealDictCursor
import sqlparse
from mcp.server.fastmcp import FastMCP

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("PostgresMCP")

mcp = FastMCP("enterprise-postgres-guard")

DB_HOST = os.getenv("PG_HOST", "localhost")
DB_PORT = int(os.getenv("PG_PORT", "5432"))
DB_NAME = os.getenv("PG_DATABASE", "analytics")
DB_USER = os.getenv("PG_READONLY_USER", "claude_ro")
DB_PASS = os.getenv("PG_PASSWORD", "secret")

def get_readonly_connection():
    """Establishes a connection with read-only transaction parameters and hard statement timeouts."""
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASS,
        options="-c default_transaction_read_only=on -c statement_timeout=5000"
    )
    conn.set_session(readonly=True, autocommit=True)
    return conn

def validate_readonly_ast(sql_query: str) -> None:
    """Parses SQL query Abstract Syntax Tree (AST) to strictly guarantee read-only execution."""
    parsed = sqlparse.parse(sql_query)
    if not parsed:
        raise ValueError("Invalid SQL: Unable to parse query syntax.")

    forbidden_keywords = {
        "INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "TRUNCATE", 
        "CREATE", "GRANT", "REVOKE", "EXECUTE", "REPLACE", "CALL",
        "LOCK", "MERGE", "COPY", "SET", "RESET"
    }

    for statement in parsed:
        stmt_type = statement.get_type()
        if stmt_type != "SELECT":
            raise PermissionError(f"Security Violation: Statement type '{stmt_type}' is strictly forbidden. Only SELECT permitted.")

        for token in statement.flatten():
            val = token.value.strip().upper()
            if val in forbidden_keywords:
                raise PermissionError(f"Security Violation: Prohibited DDL/DML token '{val}' detected in query.")

@mcp.tool()
def execute_safe_select(query: str, max_rows: int = 50) -> str:
    """Executes a validated, read-only SELECT query against the analytics database with hard row bounds.
    Queries are inspected via AST parser; statement timeout is enforced at 5.0 seconds.
    """
    try:
        validate_readonly_ast(query)
    except Exception as validation_err:
        logger.error(f"SQL Validation Rejected: {validation_err}")
        return json.dumps({"status": "REJECTED", "error": str(validation_err)})

    clamped_limit = min(max(max_rows, 1), 100)
    # Wrap in subquery with explicit limit to prevent unbounded memory consumption
    cleaned_query = query.strip().rstrip(";")
    bounded_query = f"SELECT * FROM ({cleaned_query}) AS __bounded_subquery LIMIT {clamped_limit};"

    conn = get_readonly_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(bounded_query)
            rows = cur.fetchall()
            return json.dumps({
                "status": "SUCCESS",
                "row_count": len(rows),
                "clamped_limit": clamped_limit,
                "data": [dict(r) for r in rows]
            }, default=str, indent=2)
    except psycopg2.extensions.QueryCanceledError:
        logger.error("Query exceeded 5.0s statement timeout.")
        return json.dumps({"status": "TIMEOUT", "error": "Query exceeded 5.0s statement execution timeout."})
    except Exception as db_err:
        logger.error(f"Database Execution Error: {db_err}")
        return json.dumps({"status": "ERROR", "error": f"Database Error: {str(db_err)}"})
    finally:
        conn.close()

@mcp.resource("postgres://{schema_name}/{table_name}/schema")
def get_table_schema(schema_name: str, table_name: str) -> str:
    """Exposes real-time PostgreSQL table column definitions, data types, and primary keys as a resource."""
    conn = get_readonly_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns
                WHERE table_schema = %s AND table_name = %s
                ORDER BY ordinal_position;
            """, (schema_name, table_name))
            columns = cur.fetchall()
            if not columns:
                return json.dumps({"error": f"Table '{schema_name}.{table_name}' not found."})
            return json.dumps({"table": f"{schema_name}.{table_name}", "columns": [dict(c) for c in columns]}, indent=2)
    finally:
        conn.close()

if __name__ == "__main__":
    mcp.run(transport="stdio")
