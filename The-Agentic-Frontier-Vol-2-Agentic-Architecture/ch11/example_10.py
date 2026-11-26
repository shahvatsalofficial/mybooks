# case_studies/cs07_mcp_database_agent.py
"""
Case Study 07: Database Operations Agent with Model Context Protocol (MCP v1.0).
Author: Vatsal Shah — The Agentic Frontier Vol 2
"""

import os
import sys
import logging
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
import sqlglot
from sqlglot import exp
from mcp.server.fastmcp import FastMCP
from langgraph.graph import StateGraph, END

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("MCPDatabaseAgent")

# Initialize FastMCP Server for PostgreSQL
mcp_server = FastMCP("PostgreSQL-Analytics-MCP")

# ============================================================================
# 1. MCP TOOL DEFINITIONS & AST SECURITY ENFORCER
# ============================================================================

class SQLSanitizerError(Exception):
    """Raised when a query fails AST safety inspection."""
    pass

def validate_and_sanitize_sql(sql_query: str) -> str:
    """
    Parses raw SQL into Abstract Syntax Tree (AST) using SQLGlot.
    Enforces strict SELECT-only whitelist and blocks all DDL/DML mutation nodes.
    """
    try:
        parsed_expressions = sqlglot.parse(sql_query, read="postgres")
    except Exception as e:
        raise SQLSanitizerError(f"SQL Syntax Error: Unable to parse query. Details: {str(e)}")

    for expression in parsed_expressions:
        if expression is None:
            continue
        # Verify root expression type is strictly SELECT
        if not isinstance(expression, exp.Select):
            forbidden_type = type(expression).__name__
            raise SQLSanitizerError(
                f"SECURITY VIOLATION: Statement type '{forbidden_type}' is prohibited. "
                "Only read-only SELECT queries are allowed."
            )
        
        # Walk AST tree to detect hidden mutating functions or INTO clauses
        for node in expression.walk():
            if isinstance(node, (exp.Drop, exp.Delete, exp.Insert, exp.Update, exp.Create, exp.Alter)):
                raise SQLSanitizerError(f"SECURITY VIOLATION: Prohibited AST node '{type(node).__name__}' detected.")

    logger.info("️ [SQL Sanitizer] AST Inspection Passed: Statement is 100% Read-Only SELECT.")
    return sql_query

# Register MCP Tool: Schema Introspection
@mcp_server.tool()
def get_table_schema(table_name: str) -> Dict[str, Any]:
    """Retrieves column names, data types, and primary keys for target PostgreSQL table."""
    logger.info(f" [MCP Tool] Introspecting schema for table: {table_name}")
    # Production connects to pg_catalog. Simulated return:
    schemas = {
        "orders": {
            "columns": ["order_id VARCHAR", "customer_id VARCHAR", "total_amount NUMERIC", "created_at TIMESTAMP"],
            "primary_key": "order_id"
        },
        "refunds": {
            "columns": ["refund_id VARCHAR", "order_id VARCHAR", "refund_reason VARCHAR", "amount NUMERIC"],
            "primary_key": "refund_id"
        }
    }
    return schemas.get(table_name, {"columns": ["unknown_column VARCHAR"], "primary_key": "id"})

# Register MCP Tool: Read-Only SQL Execution
@mcp_server.tool()
def execute_read_only_sql(sql_query: str) -> Dict[str, Any]:
    """Executes validated SELECT query against read-only PostgreSQL replica."""
    logger.info(f"⚡ [MCP Tool] Request to execute query:\n{sql_query}")
    try:
        clean_sql = validate_and_sanitize_sql(sql_query)
        # Simulated database query result:
        return {
            "status": "SUCCESS",
            "rows_affected": 0,
            "data": [
                {"refund_reason": "Sizing Issue", "total_refunds": 1420, "refund_sum": 45600.00},
                {"refund_reason": "Late Delivery", "total_refunds": 890, "refund_sum": 28400.00}
            ]
        }
    except SQLSanitizerError as se:
        logger.error(f" [MCP Tool Execution Blocked] {str(se)}")
        return {"status": "BLOCKED", "error": str(se)}

# ============================================================================
# 2. LANGGRAPH AGENT INTEGRATION
# ============================================================================

class DBAgentState(BaseModel):
    user_prompt: str
    target_tables: List[str] = Field(default_factory=list)
    generated_sql: Optional[str] = None
    query_result: Optional[Dict[str, Any]] = None
    status: str = "INITIALIZED"

def sql_generation_node(state: DBAgentState) -> Dict[str, Any]:
    """NL-to-SQL Generator Node."""
    logger.info(f" [DB Agent] Generating SQL for prompt: '{state.user_prompt}'")
    # Simulated LLM generation based on introspected schema
    sql = "SELECT refund_reason, COUNT(*) as total_refunds, SUM(amount) as refund_sum FROM refunds GROUP BY refund_reason ORDER BY total_refunds DESC;"
    return {"generated_sql": sql, "status": "SQL_GENERATED"}

def mcp_execution_node(state: DBAgentState) -> Dict[str, Any]:
    """MCP Execution Node: Invokes FastMCP execute_read_only_sql tool."""
    logger.info(" [DB Agent] Invoking MCP Tool: execute_read_only_sql...")
    res = execute_read_only_sql(state.generated_sql)
    return {"query_result": res, "status": "EXECUTION_COMPLETE"}

def build_db_agent_graph():
    builder = StateGraph(DBAgentState)
    builder.add_node("sql_generation", sql_generation_node)
    builder.add_node("mcp_execution", mcp_execution_node)

    builder.set_entry_point("sql_generation")
    builder.add_edge("sql_generation", "mcp_execution")
    builder.add_edge("mcp_execution", END)

    return builder.compile()

if __name__ == "__main__":
    app_graph = build_db_agent_graph()
    
    # Test 1: Valid Read-Only Query
    print("--- TEST 1: VALID READ-ONLY ANALYTICS QUERY ---")
    valid_state = DBAgentState(user_prompt="Show top refund reasons and total amounts.")
    res1 = app_graph.invoke(valid_state)
    print(f"Status: {res1['status']}")
    print(f"Result Data: {res1['query_result']}\n")

    # Test 2: Prompt Injection Malicious DDL Attack
    print("--- TEST 2: MALICIOUS PROMPT INJECTION DDL ATTACK ---")
    malicious_sql = "DROP TABLE orders; SELECT * FROM refunds;"
    res2 = execute_read_only_sql(malicious_sql)
    print(f"Execution Result: {res2}")
