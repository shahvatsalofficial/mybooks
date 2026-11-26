from __future__ import annotations

import re
from typing import List
from pydantic import BaseModel, Field


class PolicyCheckResult(BaseModel):
    compliant: bool
    missing_partition_filters: List[str] = Field(default_factory=list)
    pii_columns_exposed: List[str] = Field(default_factory=list)


class PartitionAndPiiEnforcer:
    """Verifies partition predicates and blocks PII column projections."""

    def check(
        self, sql: str, referenced_tables: List[str], snapshot: CatalogSnapshot
    ) -> PolicyCheckResult:
        missing_partitions: List[str] = []
        pii_exposed: List[str] = []

        where_match = re.search(r"\bWHERE\b([\s\S]*?)(?:\bGROUP\b|\bORDER\b|\bLIMIT\b|$)", sql, re.IGNORECASE)
        where_clause = where_match.group(1) if where_match else ""

        for tbl_ref in referenced_tables:
            spec = snapshot.tables.get(tbl_ref)
            if spec is None:
                # Match by short table name if schema prefix omitted
                spec = next(
                    (t for t in snapshot.tables.values() if t.table_name == tbl_ref),
                    None,
                )
            if spec is None:
                continue

            for col in spec.columns:
                if col.is_partition_key and spec.row_count_estimate >= 1_000_000:
                    if not re.search(rf"\b{re.escape(col.name)}\b", where_clause, re.IGNORECASE):
                        missing_partitions.append(f"{spec.fqn}.{col.name}")
                if col.is_pii:
                    if re.search(rf"\b{re.escape(col.name)}\b", sql, re.IGNORECASE):
                        pii_exposed.append(f"{spec.fqn}.{col.name}")

        return PolicyCheckResult(
            compliant=(len(missing_partitions) == 0 and len(pii_exposed) == 0),
            missing_partition_filters=missing_partitions,
            pii_columns_exposed=pii_exposed,
        )


async def demo_policy_enforcer() -> None:
    snap = await LiveCatalogIntrospector().get_snapshot()
    enforcer = PartitionAndPiiEnforcer()
    bad_sql = "SELECT m.merchant_name, m.tax_id, SUM(s.amount_cents) FROM analytics.settlement_events s JOIN analytics.merchants m ON s.merchant_id = m.id GROUP BY 1, 2 LIMIT 50;"
    res = enforcer.check(bad_sql, ["analytics.settlement_events", "analytics.merchants"], snap)
    print(f"Compliant: {res.compliant}")
    print(f"Missing partition filters: {res.missing_partition_filters}")
    print(f"PII columns exposed: {res.pii_columns_exposed}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(demo_policy_enforcer())
