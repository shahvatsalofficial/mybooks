import re
from typing import Tuple

class SafeSQLAgentGuard:
    """Enforces read-only AST safety on agent-generated SQL queries."""

    FORBIDDEN_MUTATION_REGEX = re.compile(
        r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|TRUNCATE|CREATE|GRANT|REVOKE|EXEC|MERGE)\b",
        re.IGNORECASE
    )
    LIMIT_CLAUSE_REGEX = re.compile(r"\bLIMIT\s+(\d+)\b", re.IGNORECASE)

    @classmethod
    def validate_query(cls, sql_query: str, max_limit: int = 100) -> Tuple[bool, str]:
        # 1. Detect illegal write or DDL operations
        mutation_match = cls.FORBIDDEN_MUTATION_REGEX.search(sql_query)
        if mutation_match:
            return False, f"MUTATION_REJECTED: Statement contains forbidden keyword '{mutation_match.group(0)}'."
            
        # 2. Must begin with SELECT
        trimmed = sql_query.strip()
        if not trimmed.upper().startswith("SELECT"):
            return False, "INVALID_QUERY: Query must begin with SELECT."
            
        # 3. Must enforce a LIMIT clause
        limit_match = cls.LIMIT_CLAUSE_REGEX.search(sql_query)
        if not limit_match:
            return False, "LIMIT_MISSING: Query must enforce a LIMIT clause."
            
        limit_val = int(limit_match.group(1))
        if limit_val > max_limit:
            return False, f"LIMIT_EXCEEDED: Requested limit {limit_val} exceeds maximum allowed ({max_limit})."
            
        return True, "APPROVED_READ_ONLY"

if __name__ == "__main__":
    bad_query = "SELECT * FROM users; DROP TABLE audits; --"
    ok, reason = SafeSQLAgentGuard.validate_query(bad_query)
    print(f"Malicious query check: {ok} ({reason})")
    
    good_query = "SELECT customer_id, order_total FROM orders WHERE status = 'shipped' LIMIT 50;"
    ok_good, reason_good = SafeSQLAgentGuard.validate_query(good_query)
    print(f"Legitimate query check: {ok_good} ({reason_good})")
