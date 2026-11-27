"""
Dynamic PostgreSQL Schema Reflection Engine & First-Class MCP Resource Generator
Author: Vatsal Shah | Vatsal Shah
Runtime: Python 3.11+ with FastMCP & asyncpg
"""

import os
import json
import logging
import asyncpg
from typing import Dict, Any, List
from mcp.server.fastmcp import FastMCP, Context

logger = logging.getLogger("mcp.db.schema_extractor")
mcp = FastMCP("PostgreSQL-Schema-Reflection-Gateway")

# Global In-Memory Schema Catalog Cache
SCHEMA_CATALOG: Dict[str, Dict[str, Any]] = {}

SENSITIVE_COLUMN_PATTERNS = {
    "password", "passwd", "secret", "token", "salt", "ssn", "hash", "private_key"
}

async def introspect_database_catalog(dsn: str):
    """Extract tables, columns, primary keys, and foreign keys from PostgreSQL catalogs."""
    logger.info("Extracting live schema graph from PostgreSQL system catalogs...")
    conn = await asyncpg.connect(dsn)
    try:
        # 1. Query Tables & Columns
        columns_query = """
            SELECT table_name, column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_schema = 'public'
            ORDER BY table_name, ordinal_position;
        """
        rows = await conn.fetch(columns_query)
        
        for r in rows:
            t_name = r["table_name"]
            c_name = r["column_name"]
            d_type = r["data_type"]
            nullable = r["is_nullable"] == "YES"
            
            # Filter sensitive columns
            if any(pat in c_name.lower() for pat in SENSITIVE_COLUMN_PATTERNS):
                logger.debug(f"Redacting sensitive column: {t_name}.{c_name}")
                continue
                
            if t_name not in SCHEMA_CATALOG:
                SCHEMA_CATALOG[t_name] = {"columns": [], "foreign_keys": []}
                
            SCHEMA_CATALOG[t_name]["columns"].append({
                "name": c_name,
                "type": d_type,
                "nullable": nullable
            })
            
        # 2. Query Foreign Key Constraints
        fk_query = """
            SELECT
                tc.table_name AS source_table,
                kcu.column_name AS source_column,
                ccu.table_name AS target_table,
                ccu.column_name AS target_column
            FROM information_schema.table_constraints AS tc
            JOIN information_schema.key_column_usage AS kcu
              ON tc.constraint_name = kcu.constraint_name
            JOIN information_schema.constraint_column_usage AS ccu
              ON ccu.constraint_name = tc.constraint_name
            WHERE tc.constraint_type = 'FOREIGN KEY' AND tc.table_schema = 'public';
        """
        fk_rows = await conn.fetch(fk_query)
        for fk in fk_rows:
            s_table = fk["source_table"]
            if s_table in SCHEMA_CATALOG:
                SCHEMA_CATALOG[s_table]["foreign_keys"].append({
                    "column": fk["source_column"],
                    "references_table": fk["target_table"],
                    "references_column": fk["target_column"]
                })
                
        logger.info(f"Introspection Complete: Indexed {len(SCHEMA_CATALOG)} public tables.")
    finally:
        await conn.close()


@mcp.resource("db://schema/{table_name}")
async def get_table_schema_resource(table_name: str) -> str:
    """Exposes table schema metadata as a first-class MCP resource."""
    normalized_name = table_name.strip().lower()
    if normalized_name not in SCHEMA_CATALOG:
        return json.dumps({
            "error": f"Table '{normalized_name}' not found in public database schema catalog.",
            "available_tables": list(SCHEMA_CATALOG.keys())
        }, indent=2)
        
    return json.dumps({
        "table": normalized_name,
        "schema": SCHEMA_CATALOG[normalized_name]
    }, indent=2)


@mcp.prompt("sql_copilot")
async def generate_sql_copilot_prompt(table_context: str = "orders") -> str:
    """Injects current table schema definitions directly into model reasoning prompt."""
    target = table_context.strip().lower()
    table_data = SCHEMA_CATALOG.get(target, {"columns": [], "foreign_keys": []})
    
    prompt_lines = [
        f"You are an expert SQL analytics copilot querying the '{target}' table.",
        "Strictly follow these schema rules:",
        "1. Only reference columns verified in the table definition below.",
        "2. Never execute destructive DDL (DROP, ALTER) or write queries (UPDATE, DELETE).",
        "3. Always supply indexed filter predicates to prevent full table scans.",
        "",
        f"=== SCHEMA DEFINITION FOR TABLE: {target} ==="
    ]
    
    for col in table_data.get("columns", []):
        prompt_lines.append(f"- {col['name']} ({col['type']}) | Nullable: {col['nullable']}")
        
    if table_data.get("foreign_keys"):
        prompt_lines.append("\n=== VERIFIED FOREIGN KEY RELATIONSHIPS ===")
        for fk in table_data["foreign_keys"]:
            prompt_lines.append(f"- {fk['column']} -> references {fk['references_table']}.{fk['references_column']}")
            
    return "\n".join(prompt_lines)
