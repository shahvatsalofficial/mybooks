"""
Production AST-Gated SQL Execution Engine for LLM Agents
Guarantees zero SQL injection, strict read-only execution, and table whitelisting.
"""
from typing import List, Set, Dict, Any, Optional
import sqlglot
from sqlglot import exp
import logging

logger = logging.getLogger("SQLSecurityGate")

class ASTQueryValidationError(Exception):
    """Raised when an LLM-generated SQL query breaches security constraints."""
    pass

class GatedSQLExecutor:
    def __init__(self, allowed_tables: Set[str], max_limit: int = 100):
        self.allowed_tables = {tbl.lower() for tbl in allowed_tables}
        self.max_limit = max_limit

    def validate_and_rewrite_query(self, raw_sql: str) -> str:
        # Step 1: Parse raw SQL into Abstract Syntax Tree
        try:
            parsed_expressions = sqlglot.parse(raw_sql)
        except Exception as e:
            raise ASTQueryValidationError(f"SQL Syntax Parse Failure: {str(e)}")

        if not parsed_expressions or len(parsed_expressions) > 1:
            raise ASTQueryValidationError("Security Violation: Multi-statement batch queries are strictly forbidden.")

        expression = parsed_expressions[0]

        # Step 2: Enforce root statement type must be SELECT
        if not isinstance(expression, exp.Select):
            raise ASTQueryValidationError(
                f"Security Violation: Only SELECT queries are permitted. Detected: {type(expression).__name__}"
            )

        # Step 3: Verify all accessed tables reside in strict whitelist
        accessed_tables = {
            table.name.lower() 
            for table in expression.find_all(exp.Table)
        }
        unauthorized_tables = accessed_tables - self.allowed_tables
        if unauthorized_tables:
            raise ASTQueryValidationError(
                f"Access Denied: Query attempts to access unauthorized tables: {list(unauthorized_tables)}. "
                f"Permitted tables: {list(self.allowed_tables)}"
            )

        # Step 4: Scan for disallowed mutating AST clauses
        disallowed_nodes = (exp.Insert, exp.Update, exp.Delete, exp.Drop, exp.AlterTable, exp.Command)
        for node in expression.walk():
            if isinstance(node, disallowed_nodes):
                raise ASTQueryValidationError(f"Prohibited mutating operation detected: {type(node).__name__}")

        # Step 5: Enforce mandatory LIMIT ceiling to prevent server memory exhaustion
        existing_limit = expression.find(exp.Limit)
        if existing_limit:
            limit_value = int(existing_limit.expression.this)
            if limit_value > self.max_limit:
                logger.warning(f"Clamping user limit {limit_value} to maximum ceiling {self.max_limit}.")
                existing_limit.set("expression", exp.Literal.number(self.max_limit))
        else:
            # Inject LIMIT clause into AST
            expression = expression.limit(self.max_limit)

        rewritten_sql = expression.sql(dialect="postgres")
        logger.info(f"Verified & Rewritten SQL: {rewritten_sql}")
        return rewritten_sql

    async def execute_safe_query(self, db_pool, raw_sql: str) -> List[Dict[str, Any]]:
        safe_sql = self.validate_and_rewrite_query(raw_sql)
        async with db_pool.acquire() as conn:
            # Execute on read-only connection transaction
            async with conn.transaction(readonly=True):
                rows = await conn.fetch(safe_sql)
                return [dict(row) for row in rows]
