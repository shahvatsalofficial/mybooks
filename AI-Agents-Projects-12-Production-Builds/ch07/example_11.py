from __future__ import annotations

import json
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class DbtNodeInfo(BaseModel):
    unique_id: str
    name: str
    resource_type: str
    schema_name: str
    relation_name: str
    depends_on: List[str] = Field(default_factory=list)
    compiled_code: str = ""


class DbtRunFailure(BaseModel):
    unique_id: str
    status: str
    message: str
    execution_time_s: float


class DbtArtifactBundle(BaseModel):
    nodes: Dict[str, DbtNodeInfo] = Field(default_factory=dict)
    failures: List[DbtRunFailure] = Field(default_factory=list)


class DbtArtifactParser:
    """Parses dbt manifest.json and run_results.json into typed DAG structures."""

    def parse(self, manifest_json: str, run_results_json: str) -> DbtArtifactBundle:
        manifest = json.loads(manifest_json)
        run_results = json.loads(run_results_json)

        nodes: Dict[str, DbtNodeInfo] = {}
        for uid, raw in manifest.get("nodes", {}).items():
            nodes[uid] = DbtNodeInfo(
                unique_id=uid,
                name=raw.get("name", uid),
                resource_type=raw.get("resource_type", "model"),
                schema_name=raw.get("schema", "analytics"),
                relation_name=raw.get("relation_name", uid),
                depends_on=raw.get("depends_on", {}).get("nodes", []),
                compiled_code=raw.get("compiled_code", ""),
            )

        failures: List[DbtRunFailure] = []
        for res in run_results.get("results", []):
            status = res.get("status", "success")
            if status in {"error", "fail"}:
                failures.append(
                    DbtRunFailure(
                        unique_id=res["unique_id"],
                        status=status,
                        message=res.get("message", ""),
                        execution_time_s=float(res.get("execution_time", 0.0)),
                    )
                )

        return DbtArtifactBundle(nodes=nodes, failures=failures)


def demo_dbt_parser() -> None:
    sample_manifest = json.dumps({"nodes": {
        "model.fintech.stg_settlements": {"name": "stg_settlements", "resource_type": "model", "schema": "staging", "relation_name": "staging.stg_settlements", "depends_on": {"nodes": []}, "compiled_code": "SELECT event_id, merchant_id, amount_cents FROM raw.card_events"},
        "model.fintech.fct_daily_settlements": {"name": "fct_daily_settlements", "resource_type": "model", "schema": "analytics", "relation_name": "analytics.fct_daily_settlements", "depends_on": {"nodes": ["model.fintech.stg_settlements"]}, "compiled_code": "SELECT merchant_id, SUM(amount_cents) FROM staging.stg_settlements GROUP BY 1"},
        "test.fintech.not_null_fct_daily_settlements_merchant_id": {"name": "not_null_fct_daily_settlements_merchant_id", "resource_type": "test", "schema": "analytics", "relation_name": "analytics.not_null_check", "depends_on": {"nodes": ["model.fintech.fct_daily_settlements"]}},
    }})
    sample_results = json.dumps({"results": [
        {"unique_id": "model.fintech.stg_settlements", "status": "error", "message": 'Database Error: column "merchant_id" does not exist in raw.card_events', "execution_time": 1.42},
        {"unique_id": "test.fintech.not_null_fct_daily_settlements_merchant_id", "status": "fail", "message": "Got 1420 results, configured to fail if != 0", "execution_time": 0.85},
    ]})
    bundle = DbtArtifactParser().parse(sample_manifest, sample_results)
    print(f"Loaded {len(bundle.nodes)} manifest nodes | Failures: {len(bundle.failures)}")
    for fail in bundle.failures:
        print(f"  [{fail.status.upper()}] {fail.unique_id}: {fail.message}")


if __name__ == "__main__":
    demo_dbt_parser()
