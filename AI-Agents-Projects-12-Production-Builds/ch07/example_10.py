from __future__ import annotations

import asyncio
import datetime
import decimal
import time
import uuid
from typing import Any, Dict, List
from pydantic import BaseModel, Field


class QueryExecutionResult(BaseModel):
    row_count: int
    truncated: bool
    elapsed_ms: float
    rows: List[Dict[str, Any]] = Field(default_factory=list)


class SandboxedSqlExecutor:
    """Enforces statement_timeout, row caps, and JSON-safe serialization."""

    def __init__(self, timeout_ms: int = 8000, max_rows: int = 200) -> None:
        self.timeout_ms = timeout_ms
        self.max_rows = max_rows

    @staticmethod
    def _serialize_value(val: Any) -> Any:
        if isinstance(val, (datetime.date, datetime.datetime)):
            return val.isoformat()
        if isinstance(val, decimal.Decimal):
            return float(val)
        if isinstance(val, uuid.UUID):
            return str(val)
        return val

    async def execute_readonly(self, sql: str) -> QueryExecutionResult:
        t0 = time.perf_counter()

        async def _run_db_query() -> List[Dict[str, Any]]:
            # Simulates SET LOCAL statement_timeout = 8000; READ ONLY transaction
            await asyncio.sleep(0.025)
            return [
                {
                    "category_name": "Retail",
                    "failed_cnt": 1842,
                    "total_usd": decimal.Decimal("142890.50"),
                    "last_event": datetime.date(2026, 8, 19),
                },
                {
                    "category_name": "Travel",
                    "failed_cnt": 914,
                    "total_usd": decimal.Decimal("98412.15"),
                    "last_event": datetime.date(2026, 8, 19),
                },
            ]

        raw_rows = await asyncio.wait_for(
            _run_db_query(), timeout=self.timeout_ms / 1000.0
        )
        truncated = len(raw_rows) > self.max_rows
        sliced = raw_rows[: self.max_rows]
        clean_rows = [
            {k: self._serialize_value(v) for k, v in row.items()} for row in sliced
        ]
        elapsed = (time.perf_counter() - t0) * 1000.0
        return QueryExecutionResult(
            row_count=len(clean_rows),
            truncated=truncated,
            elapsed_ms=round(elapsed, 2),
            rows=clean_rows,
        )


async def demo_executor() -> None:
    executor = SandboxedSqlExecutor(timeout_ms=5000, max_rows=100)
    res = await executor.execute_readonly("SELECT category_name, failed_cnt FROM ... LIMIT 100;")
    print(f"Rows: {res.row_count} | Truncated: {res.truncated} | Latency: {res.elapsed_ms} ms")
    print(f"First row: {res.rows[0]}")


if __name__ == "__main__":
    asyncio.run(demo_executor())
