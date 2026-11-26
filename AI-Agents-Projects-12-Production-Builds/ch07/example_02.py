from __future__ import annotations

from collections import deque
from typing import Dict, List, Set, Tuple
from pydantic import BaseModel


class JoinStep(BaseModel):
    left_table: str
    left_column: str
    right_table: str
    right_column: str

    def to_sql_clause(self) -> str:
        return (
            f"JOIN {self.right_table} ON "
            f"{self.left_table}.{self.left_column} = {self.right_table}.{self.right_column}"
        )


class SchemaJoinGraph:
    """Computes deterministic shortest foreign-key join paths between tables."""

    def __init__(self, snapshot: CatalogSnapshot) -> None:
        self.adj: Dict[str, List[JoinStep]] = {fqn: [] for fqn in snapshot.tables}
        for table in snapshot.tables.values():
            for fk in table.foreign_keys:
                if fk.source_table in self.adj and fk.target_table in self.adj:
                    self.adj[fk.source_table].append(
                        JoinStep(
                            left_table=fk.source_table,
                            left_column=fk.source_column,
                            right_table=fk.target_table,
                            right_column=fk.target_column,
                        )
                    )
                    self.adj[fk.target_table].append(
                        JoinStep(
                            left_table=fk.target_table,
                            left_column=fk.target_column,
                            right_table=fk.source_table,
                            right_column=fk.source_column,
                        )
                    )

    def shortest_path(self, start_table: str, end_table: str) -> List[JoinStep]:
        if start_table == end_table:
            return []
        if start_table not in self.adj or end_table not in self.adj:
            raise ValueError(f"Unknown table in join request: {start_table} -> {end_table}")

        visited: Set[str] = {start_table}
        queue: deque[Tuple[str, List[JoinStep]]] = deque([(start_table, [])])

        while queue:
            current, path = queue.popleft()
            for edge in self.adj[current]:
                if edge.right_table == end_table:
                    return path + [edge]
                if edge.right_table not in visited:
                    visited.add(edge.right_table)
                    queue.append((edge.right_table, path + [edge]))

        raise LookupError(f"No foreign-key join path between {start_table} and {end_table}")

    def resolve_multi_table_joins(self, tables: List[str]) -> List[JoinStep]:
        if len(tables) <= 1:
            return []
        root = tables[0]
        seen_tables: Set[str] = {root}
        resolved_steps: List[JoinStep] = []
        for target in tables[1:]:
            if target in seen_tables:
                continue
            path = self.shortest_path(root, target)
            for step in path:
                if step.right_table not in seen_tables:
                    resolved_steps.append(step)
                    seen_tables.add(step.right_table)
        return resolved_steps


async def demo_join_graph() -> None:
    snap = await LiveCatalogIntrospector().get_snapshot()
    graph = SchemaJoinGraph(snap)
    joins = graph.resolve_multi_table_joins(
        ["analytics.settlement_events", "analytics.merchant_categories"]
    )
    print(f"Resolved {len(joins)} join hops:")
    for step in joins:
        print(f"  {step.to_sql_clause()}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(demo_join_graph())
