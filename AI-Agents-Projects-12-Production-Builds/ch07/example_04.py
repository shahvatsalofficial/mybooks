from __future__ import annotations

import re
from typing import List, Optional, Set
from pydantic import BaseModel, Field


FORBIDDEN_KEYWORDS: Set[str] = {
    "INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "TRUNCATE",
    "CREATE", "REPLACE", "MERGE", "GRANT", "REVOKE", "COPY",
    "CALL", "EXEC", "EXECUTE", "VACUUM", "ATTACH", "DETACH",
}


class AstValidationResult(BaseModel):
    is_valid: bool
    normalized_sql: str
    violations: List[str] = Field(default_factory=list)
    referenced_tables: List[str] = Field(default_factory=list)
    has_limit: bool = False
    limit_value: Optional[int] = None


class DeterministicSqlAstValidator:
    """Validates read-only SQL safety, statement singularity, and LIMIT bounds."""

    def __init__(self, max_limit: int = 1000, allow_select_star: bool = False) -> None:
        self.max_limit = max_limit
        self.allow_select_star = allow_select_star

    @staticmethod
    def _strip_comments_and_strings(sql: str) -> Tuple[str, List[str]]:
        # Remove single-line and block comments while preserving string literals safely
        cleaned = re.sub(r"/\*[\s\S]*?\*/", " ", sql)
        cleaned = re.sub(r"--[^\n]*", " ", cleaned)
        no_strings = re.sub(r"'(?:''|[^'])*'", "''", cleaned)
        return cleaned.strip(), re.findall(r"[A-Za-z_][A-Za-z0-9_]*", no_strings.upper())

    def validate(self, sql: str) -> AstValidationResult:
        violations: List[str] = []
        cleaned, upper_tokens = self._strip_comments_and_strings(sql)
        if not cleaned:
            return AstValidationResult(
                is_valid=False, normalized_sql="", violations=["Empty SQL statement."]
            )

        # 1. Reject stacked statements (semicolon followed by non-whitespace)
        stripped_trailing = cleaned.rstrip(";").strip()
        if ";" in stripped_trailing:
            violations.append("Multiple stacked SQL statements are prohibited.")

        # 2. Enforce SELECT or WITH root verb
        if not upper_tokens or upper_tokens[0] not in {"SELECT", "WITH"}:
            violations.append(
                f"Root statement must be SELECT or WITH, got: {upper_tokens[0] if upper_tokens else 'NONE'}."
            )

        # 3. Reject any forbidden DDL/DML keyword anywhere in the AST tokens
        found_forbidden = sorted(set(upper_tokens) & FORBIDDEN_KEYWORDS)
        if found_forbidden:
            violations.append(f"Forbidden write/DDL keywords detected: {found_forbidden}")

        # 4. Block SELECT * unless explicitly permitted
        if not self.allow_select_star and re.search(r"\bSELECT\s+(?:DISTINCT\s+)?\*", cleaned, re.IGNORECASE):
            violations.append("Unbounded SELECT * is prohibited; specify explicit projection columns.")

        # 5. Extract referenced tables
        tables = re.findall(
            r"\b(?:FROM|JOIN)\s+([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)?)",
            cleaned,
            re.IGNORECASE,
        )

        # 6. Check and enforce LIMIT ceiling
        limit_match = re.search(r"\bLIMIT\s+(\d+)\b", cleaned, re.IGNORECASE)
        limit_val: Optional[int] = int(limit_match.group(1)) if limit_match else None
        normalized = stripped_trailing
        if limit_val is None:
            normalized = f"{normalized}\nLIMIT {self.max_limit}"
            limit_val = self.max_limit
            has_limit = True
        elif limit_val > self.max_limit:
            violations.append(f"LIMIT {limit_val} exceeds max allowed ceiling of {self.max_limit}.")
            has_limit = True
        else:
            has_limit = True

        return AstValidationResult(
            is_valid=len(violations) == 0,
            normalized_sql=normalized + ";",
            violations=violations,
            referenced_tables=sorted(set(tables)),
            has_limit=has_limit,
            limit_value=limit_val,
        )


def demo_ast_validator() -> None:
    validator = DeterministicSqlAstValidator(max_limit=500)
    safe_sql = """
    SELECT mc.category_name, COUNT(*) AS failed_cnt
    FROM analytics.settlement_events s
    JOIN analytics.merchants m ON s.merchant_id = m.id
    JOIN analytics.merchant_categories mc ON m.category_id = mc.id
    WHERE s.settled_date >= '2026-08-01' AND s.status = 'failed'
    GROUP BY mc.category_name
    """
    unsafe_sql = "SELECT * FROM analytics.merchants; DROP TABLE analytics.merchants;"
    res_safe = validator.validate(safe_sql)
    res_unsafe = validator.validate(unsafe_sql)
    print(f"Safe SQL valid: {res_safe.is_valid} | Auto-LIMIT: {res_safe.limit_value} | Tables: {res_safe.referenced_tables}")
    print(f"Unsafe SQL valid: {res_unsafe.is_valid} | Violations: {res_unsafe.violations}")


if __name__ == "__main__":
    demo_ast_validator()
