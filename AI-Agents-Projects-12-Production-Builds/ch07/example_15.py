from __future__ import annotations

import asyncio
import json
import time
from typing import Any, Dict, List
from pydantic import BaseModel, Field


class AgentQueryResponse(BaseModel):
    question: str
    approved: bool
    final_sql: str
    row_count: int
    rows: List[Dict[str, Any]] = Field(default_factory=list)
    total_latency_ms: float
    warnings: List[str] = Field(default_factory=list)


class DataPipelineAgent:
    """End-to-end schema-grounded SQL synthesis and guardrail orchestrator."""

    def __init__(self) -> None:
        self.introspector = LiveCatalogIntrospector(ttl_seconds=300)
        self.ast_validator = DeterministicSqlAstValidator(max_limit=500)
        self.explain_guard = ExplainCostGuardrail(max_total_cost=250_000.0)
        self.policy_enforcer = PartitionAndPiiEnforcer()
        self.executor = SandboxedSqlExecutor(timeout_ms=8000, max_rows=200)

    async def answer_question(self, question: str, candidate_sql: str) -> AgentQueryResponse:
        t0 = time.perf_counter()
        snapshot = await self.introspector.get_snapshot()

        def _reject(sql_str: str, msgs: List[str]) -> AgentQueryResponse:
            return AgentQueryResponse(
                question=question, approved=False, final_sql=sql_str, row_count=0,
                total_latency_ms=round((time.perf_counter() - t0) * 1000, 2), warnings=msgs,
            )

        ast_res = self.ast_validator.validate(candidate_sql)
        if not ast_res.is_valid:
            return _reject(candidate_sql, ast_res.violations)

        policy_res = self.policy_enforcer.check(ast_res.normalized_sql, ast_res.referenced_tables, snapshot)
        if not policy_res.compliant:
            msgs = []
            if policy_res.missing_partition_filters:
                msgs.append(f"Missing partition filters: {policy_res.missing_partition_filters}")
            if policy_res.pii_columns_exposed:
                msgs.append(f"PII columns blocked: {policy_res.pii_columns_exposed}")
            return _reject(ast_res.normalized_sql, msgs)

        sim_plan = json.dumps([{"Plan": {"Node Type": "Limit", "Total Cost": 3420.5, "Plan Rows": 120, "Plans": [{"Node Type": "Index Scan", "Relation Name": "settlement_events", "Total Cost": 3400.0, "Plan Rows": 48000}]}}])
        explain_res = await self.explain_guard.evaluate_plan(ast_res.normalized_sql, snapshot, sim_plan)
        if not explain_res.approved:
            return _reject(ast_res.normalized_sql, [explain_res.rejection_reason])

        exec_res = await self.executor.execute_readonly(ast_res.normalized_sql)
        return AgentQueryResponse(
            question=question, approved=True, final_sql=ast_res.normalized_sql,
            row_count=exec_res.row_count, rows=exec_res.rows,
            total_latency_ms=round((time.perf_counter() - t0) * 1000, 2),
        )


async def demo_agent() -> None:
    agent = DataPipelineAgent()
    sql = (
        "SELECT mc.category_name, COUNT(*) AS failed_cnt, SUM(s.amount_cents)/100.0 AS total_usd "
        "FROM analytics.settlement_events s "
        "JOIN analytics.merchants m ON s.merchant_id = m.id "
        "JOIN analytics.merchant_categories mc ON m.category_id = mc.id "
        "WHERE s.settled_date >= '2026-06-01' AND s.status = 'failed' "
        "GROUP BY mc.category_name ORDER BY failed_cnt DESC"
    )
    resp = await agent.answer_question("Failed card settlements by category last 90 days", sql)
    print(f"Approved: {resp.approved} | Rows: {resp.row_count} | Latency: {resp.total_latency_ms} ms")
    print(f"Top result: {resp.rows[0]}")


if __name__ == "__main__":
    asyncio.run(demo_agent())
