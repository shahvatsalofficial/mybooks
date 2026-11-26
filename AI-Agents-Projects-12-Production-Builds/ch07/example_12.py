from __future__ import annotations

from typing import Dict, List, Set
from pydantic import BaseModel, Field


class LineageTriageReport(BaseModel):
    root_cause_nodes: List[str] = Field(default_factory=list)
    cascading_victims: List[str] = Field(default_factory=list)
    blast_radius_map: Dict[str, List[str]] = Field(default_factory=dict)


class UpstreamLineageIsolator:
    """Identifies earliest failing upstream ancestors in a dbt DAG."""

    def isolate(self, bundle: DbtArtifactBundle) -> LineageTriageReport:
        failed_ids: Set[str] = {f.unique_id for f in bundle.failures}
        root_causes: List[str] = []
        cascading: List[str] = []

        # Build reverse adjacency (parent -> children) for blast-radius mapping
        children_map: Dict[str, List[str]] = {uid: [] for uid in bundle.nodes}
        for uid, node in bundle.nodes.items():
            for parent in node.depends_on:
                if parent in children_map:
                    children_map[parent].append(uid)

        def has_failing_ancestor(uid: str, visited: Set[str]) -> bool:
            node = bundle.nodes.get(uid)
            if not node:
                return False
            for parent in node.depends_on:
                if parent in visited:
                    continue
                visited.add(parent)
                if parent in failed_ids or has_failing_ancestor(parent, visited):
                    return True
            return False

        for f_uid in sorted(failed_ids):
            if has_failing_ancestor(f_uid, set()):
                cascading.append(f_uid)
            else:
                root_causes.append(f_uid)

        blast_map: Dict[str, List[str]] = {}
        for rc in root_causes:
            descendants: List[str] = []
            stack = list(children_map.get(rc, []))
            seen: Set[str] = set()
            while stack:
                curr = stack.pop(0)
                if curr not in seen:
                    seen.add(curr)
                    descendants.append(curr)
                    stack.extend(children_map.get(curr, []))
            blast_map[rc] = descendants

        return LineageTriageReport(
            root_cause_nodes=root_causes,
            cascading_victims=cascading,
            blast_radius_map=blast_map,
        )


def demo_lineage_isolator() -> None:
    bundle = DbtArtifactBundle(
        nodes={
            "model.fintech.stg_settlements": DbtNodeInfo(unique_id="model.fintech.stg_settlements", name="stg_settlements", resource_type="model", schema_name="staging", relation_name="staging.stg_settlements", depends_on=[]),
            "model.fintech.fct_daily_settlements": DbtNodeInfo(unique_id="model.fintech.fct_daily_settlements", name="fct_daily_settlements", resource_type="model", schema_name="analytics", relation_name="analytics.fct_daily_settlements", depends_on=["model.fintech.stg_settlements"]),
            "test.fintech.not_null_fct_daily_settlements_merchant_id": DbtNodeInfo(unique_id="test.fintech.not_null_fct_daily_settlements_merchant_id", name="not_null_fct_daily_settlements_merchant_id", resource_type="test", schema_name="analytics", relation_name="analytics.not_null_check", depends_on=["model.fintech.fct_daily_settlements"]),
        },
        failures=[
            DbtRunFailure(unique_id="model.fintech.stg_settlements", status="error", message="missing col", execution_time_s=1.2),
            DbtRunFailure(unique_id="test.fintech.not_null_fct_daily_settlements_merchant_id", status="fail", message="nulls", execution_time_s=0.7),
        ],
    )
    report = UpstreamLineageIsolator().isolate(bundle)
    print(f"Root causes: {report.root_cause_nodes}")
    print(f"Cascading victims: {report.cascading_victims}")
    print(f"Blast radius: {report.blast_radius_map}")


if __name__ == "__main__":
    demo_lineage_isolator()
