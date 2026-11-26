"""
Guardrail Conformance Auditor.
Executes pre-flight syntactic and semantic checks on agent outputs prior to tool dispatch.
"""

import re
from typing import Tuple, Optional


class GuardrailConformanceAuditor:
    """Enforces absolute invariants before releasing tool payloads."""

    SQL_MUTATION_REGEX = re.compile(r"\b(DROP|TRUNCATE|DELETE|ALTER)\b", re.IGNORECASE)

    @classmethod
    def audit_sql_action(cls, query_string: str) -> Tuple[bool, Optional[str]]:
        """Blocks unverified destructive SQL queries."""
        match = cls.SQL_MUTATION_REGEX.search(query_string)
        if match:
            return False, f"MUTATION_BLOCKED: Destructive SQL keyword '{match.group(1)}' detected."
        return True, None
