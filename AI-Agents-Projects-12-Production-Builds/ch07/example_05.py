from __future__ import annotations

import asyncio
import json
from typing import Any, Dict, List
from pydantic import BaseModel, Field


class ExplainCostAssessment(BaseModel):
    approved: bool
    total_cost: float
    estimated_rows: int
    seq_scans_on_large_tables: List[str] = Field(default_factory=list)
    rejection_reason: str = ""


class ExplainCostGuardrail:
    """Evaluates database EXPLAIN JSON plans against cost and scan thresholds."""

    def __init__(
        self,
        max_total_cost: float = 250_000.0,
        max_estimated_rows: int = 5_000_000,
        large_table_threshold: int = 1_000_000,
    ) -> None:
        self.max_total_cost = max_total_cost
        self.max_estimated_rows = max_estimated_rows
        self.large_table_threshold = large_table_threshold

    def _walk_plan(
        self,
        node: Dict[str, Any],
        snapshot: CatalogSnapshot,
        seq_scans: List[str],
    ) -> None:
        node_type = node.get("Node Type", "")
        rel_name = node.get("Relation Name", "")
        if node_type == "Seq Scan" and rel_name:
            for fqn, spec in snapshot.tables.items():
                if spec.table_name == rel_name and spec.row_count_estimate >= self.large_table_threshold:
                    seq_scans.append(fqn)
        for child in node.get("Plans", []):
            self._walk_plan(child, snapshot, seq_scans)

    async def evaluate_plan(
        self, sql: str, snapshot: CatalogSnapshot, simulated_plan_json: str
    ) -> ExplainCostAssessment:
        await asyncio.sleep(0.012)
        parsed = json.loads(simulated_plan_json)
        root_plan = parsed[0]["Plan"]
        total_cost = float(root_plan.get("Total Cost", 0.0))
        est_rows = int(root_plan.get("Plan Rows", 0))
        seq_scans: List[str] = []
        self._walk_plan(root_plan, snapshot, seq_scans)

        reasons: List[str] = []
        if total_cost > self.max_total_cost:
            reasons.append(f"Total Cost {total_cost:,.1f} exceeds budget {self.max_total_cost:,.1f}.")
        if est_rows > self.max_estimated_rows:
            reasons.append(f"Estimated rows {est_rows:,} exceeds cap {self.max_estimated_rows:,}.")
        if seq_scans:
            reasons.append(f"Unbounded Seq Scan on large table(s): {seq_scans}.")

        return ExplainCostAssessment(
            approved=len(reasons) == 0,
            total_cost=total_cost,
            estimated_rows=est_rows,
            seq_scans_on_large_tables=seq_scans,
            rejection_reason=" ".join(reasons),
        )


async def demo_explain_guard() -> None:
    snap = await LiveCatalogIntrospector().get_snapshot()
    guard = ExplainCostGuardrail(max_total_cost=150_000.0)
    bad_plan = json.dumps([{
        "Plan": {
            "Node Type": "Limit",
            "Total Cost": 984210.5,
            "Plan Rows": 100,
            "Plans": [{
                "Node Type": "Seq Scan",
                "Relation Name": "settlement_events",
                "Total Cost": 984000.0,
                "Plan Rows": 4200000000,
            }],
        }
    }])
    good_plan = json.dumps([{
        "Plan": {
            "Node Type": "Limit",
            "Total Cost": 1420.4,
            "Plan Rows": 45,
            "Plans": [{
                "Node Type": "Index Scan",
                "Relation Name": "settlement_events",
                "Total Cost": 1410.0,
                "Plan Rows": 18500,
            }],
        }
    }])
    res_bad = await guard.evaluate_plan("SELECT ...", snap, bad_plan)
    res_good = await guard.evaluate_plan("SELECT ...", snap, good_plan)
    print(f"Bad plan approved: {res_bad.approved} | Reason: {res_bad.rejection_reason}")
    print(f"Good plan approved: {res_good.approved} | Cost: {res_good.total_cost:.1f} | Rows: {res_good.estimated_rows}")


if __name__ == "__main__":
    asyncio.run(demo_explain_guard())
