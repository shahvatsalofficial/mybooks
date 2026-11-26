from __future__ import annotations

import re
from typing import List


def rewrite_case_insensitive_filter(
    sql: str, suggestions: List[LiteralProbeSuggestion]
) -> str:
    updated = sql
    for item in suggestions:
        if item.suggested_replacement:
            pattern = re.compile(
                rf"({re.escape(item.column)}\s*=\s*)'{re.escape(item.queried_value)}'"
            )
            updated = pattern.sub(rf"\1'{item.suggested_replacement}'", updated)
    return updated


if __name__ == "__main__":
    sample_sql = "SELECT COUNT(*) FROM analytics.settlement_events s WHERE s.status = 'Failed' LIMIT 100;"
    sugg = [
        LiteralProbeSuggestion(
            column="s.status",
            queried_value="Failed",
            observed_values=["settled", "failed", "pending"],
            suggested_replacement="failed",
        )
    ]
    print(rewrite_case_insensitive_filter(sample_sql, sugg))
