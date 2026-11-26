from __future__ import annotations

import re
from typing import Dict, List, Set, Tuple
from pydantic import BaseModel, Field


class SqlExemplar(BaseModel):
    question: str
    sql: str
    tables_used: List[str]


class PrunedSchemaContext(BaseModel):
    selected_tables: List[str]
    ddl_block: str
    verified_joins: List[str]
    exemplars: List[SqlExemplar] = Field(default_factory=list)


class HybridSchemaPruner:
    """Ranks relevant tables, resolves bridge tables, and retrieves SQL exemplars."""

    def __init__(self, snapshot: CatalogSnapshot, exemplars: List[SqlExemplar]) -> None:
        self.snapshot = snapshot
        self.exemplars = exemplars
        self.join_graph = SchemaJoinGraph(snapshot)

    @staticmethod
    def _tokenize(text: str) -> Set[str]:
        return set(re.findall(r"[a-z0-9_]+", text.lower()))

    def _score_table(self, query_tokens: Set[str], table: TableSpec) -> float:
        table_tokens = self._tokenize(f"{table.table_name} {table.description}")
        col_tokens = self._tokenize(
            " ".join(f"{c.name} {c.description}" for c in table.columns)
        )
        overlap_table = len(query_tokens & table_tokens) * 2.5
        overlap_cols = len(query_tokens & col_tokens) * 1.2
        return overlap_table + overlap_cols

    def build_context(self, question: str, top_k: int = 3) -> PrunedSchemaContext:
        q_tokens = self._tokenize(question)
        scored: List[Tuple[float, str]] = []
        for fqn, table in self.snapshot.tables.items():
            score = self._score_table(q_tokens, table)
            scored.append((score, fqn))
        scored.sort(key=lambda item: item[0], reverse=True)

        primary_tables = [fqn for score, fqn in scored[:top_k] if score > 0]
        if not primary_tables:
            primary_tables = [fqn for _, fqn in scored[:top_k]]

        join_steps = self.join_graph.resolve_multi_table_joins(primary_tables)
        all_needed: List[str] = list(primary_tables)
        for step in join_steps:
            if step.right_table not in all_needed:
                all_needed.append(step.right_table)

        ddl_sections = [
            self.snapshot.tables[fqn].to_compact_ddl(mask_pii=True)
            for fqn in all_needed
        ]
        matched_exemplars = [
            ex for ex in self.exemplars
            if any(t in all_needed for t in ex.tables_used)
        ][:2]

        return PrunedSchemaContext(
            selected_tables=all_needed,
            ddl_block="\n\n".join(ddl_sections),
            verified_joins=[s.to_sql_clause() for s in join_steps],
            exemplars=matched_exemplars,
        )


async def demo_pruner() -> None:
    snap = await LiveCatalogIntrospector().get_snapshot()
    exemplars = [
        SqlExemplar(
            question="Daily settled volume by country over last 7 days",
            sql=(
                "SELECT m.country_code, SUM(s.amount_cents) / 100.0 AS usd_vol "
                "FROM analytics.settlement_events s "
                "JOIN analytics.merchants m ON s.merchant_id = m.id "
                "WHERE s.settled_date >= CURRENT_DATE - INTERVAL '7 days' "
                "AND s.status = 'settled' GROUP BY 1 LIMIT 100;"
            ),
            tables_used=["analytics.settlement_events", "analytics.merchants"],
        )
    ]
    pruner = HybridSchemaPruner(snap, exemplars)
    ctx = pruner.build_context("failed card settlements by category_name last 90 days", top_k=2)
    print(f"Selected tables (with bridge): {ctx.selected_tables}")
    print(f"Verified joins: {ctx.verified_joins}")
    print(f"Exemplars attached: {len(ctx.exemplars)}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(demo_pruner())
