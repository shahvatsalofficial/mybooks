from __future__ import annotations

import asyncio
import re
from typing import Dict, List, Tuple
from pydantic import BaseModel, Field


class LiteralProbeSuggestion(BaseModel):
    column: str
    queried_value: str
    observed_values: List[str] = Field(default_factory=list)
    suggested_replacement: str = ""


class EmptyResultGuard:
    """Probes distinct column values when a valid SQL query returns zero rows."""

    @staticmethod
    def extract_equality_filters(sql: str) -> List[Tuple[str, str]]:
        # Matches patterns like s.status = 'Failed' or category_name = 'SaaS'
        pattern = re.compile(
            r"([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)?)\s*=\s*'([^']+)'"
        )
        return pattern.findall(sql)

    async def diagnose_zero_rows(
        self,
        sql: str,
        fetch_distinct_fn: Callable[[str], Awaitable[List[str]]],
    ) -> List[LiteralProbeSuggestion]:
        filters = self.extract_equality_filters(sql)
        suggestions: List[LiteralProbeSuggestion] = []
        for col, val in filters:
            observed = await fetch_distinct_fn(col)
            if val not in observed:
                ci_match = next((o for o in observed if o.lower() == val.lower()), "")
                suggestions.append(
                    LiteralProbeSuggestion(
                        column=col,
                        queried_value=val,
                        observed_values=observed[:10],
                        suggested_replacement=ci_match,
                    )
                )
        return suggestions


async def demo_empty_guard() -> None:
    guard = EmptyResultGuard()

    async def mock_distinct(col: str) -> List[str]:
        await asyncio.sleep(0.005)
        if "status" in col:
            return ["settled", "failed", "pending"]
        return []

    sql = "SELECT COUNT(*) FROM analytics.settlement_events s WHERE s.status = 'Failed' LIMIT 100;"
    findings = await guard.diagnose_zero_rows(sql, mock_distinct)
    for f in findings:
        print(
            f"Mismatch on {f.column}: queried='{f.queried_value}', "
            f"observed={f.observed_values}, suggested='{f.suggested_replacement}'"
        )


if __name__ == "__main__":
    asyncio.run(demo_empty_guard())
