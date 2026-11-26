"""
recipe_6_1_multi_primitive_server.py
Enterprise FastMCP Server demonstrating Tools, Templated Resources, and Prompts.
"""

import sys
from typing import Optional
from mcp.server.fastmcp import FastMCP
from mcp.types import PromptMessage, TextContent, EmbeddedResource, TextResourceContents
from pydantic import BaseModel, Field

mcp = FastMCP("EnterpriseInfrastructureServer")

# Internal mock infrastructure database
CLUSTER_INVENTORY = {
    "us-east-prod": {"status": "HEALTHY", "nodes": 12, "region": "us-east-1", "cpu_utilization": 0.42},
    "eu-west-prod": {"status": "DEGRADED", "nodes": 8, "region": "eu-west-1", "cpu_utilization": 0.89},
}


class NodeDrainRequest(BaseModel):
    cluster_id: str = Field(..., description="Target Kubernetes cluster identifier.")
    grace_period_seconds: int = Field(300, ge=30, le=1800, description="Eviction grace period in seconds.")
    force: bool = Field(False, description="Force node drain ignoring PodDisruptionBudgets.")


# ─── PRIMITIVE 1: TOOLS ────────────────────────────────────────────────────────
@mcp.tool()
def drain_cluster_node(req: NodeDrainRequest) -> str:
    """Initiates a safe node drain sequence on a designated Kubernetes cluster."""
    sys.stderr.write(f"[Tools] Draining nodes on cluster {req.cluster_id}...\n")
    if req.cluster_id not in CLUSTER_INVENTORY:
        raise KeyError(f"Cluster '{req.cluster_id}' not found in active inventory.")

    cluster = CLUSTER_INVENTORY[req.cluster_id]
    return f"Node drain scheduled for {req.cluster_id} (Region: {cluster['region']}). Grace period: {req.grace_period_seconds}s."


# ─── PRIMITIVE 2: RESOURCES ────────────────────────────────────────────────────
@mcp.resource("k8s://clusters/{cluster_id}/status")
def get_cluster_status(cluster_id: str) -> str:
    """Exposes real-time telemetry state for a specific Kubernetes cluster."""
    sys.stderr.write(f"[Resources] Reading telemetry for cluster: {cluster_id}\n")
    if cluster_id not in CLUSTER_INVENTORY:
        raise KeyError(f"Cluster '{cluster_id}' does not exist.")

    data = CLUSTER_INVENTORY[cluster_id]
    return f"# Telemetry Report: {cluster_id}\nStatus: {data['status']}\nNodes: {data['nodes']}\nCPU: {data['cpu_utilization'] * 100}%"


# ─── PRIMITIVE 3: PROMPTS ──────────────────────────────────────────────────────
@mcp.prompt()
def incident_remediation_workflow(cluster_id: str) -> list[PromptMessage]:
    """Generates an incident response prompt attaching cluster telemetry."""
    if cluster_id not in CLUSTER_INVENTORY:
        raise KeyError(f"Cannot generate remediation prompt: Cluster '{cluster_id}' not found.")

    cluster_data = CLUSTER_INVENTORY[cluster_id]

    msg_instruction = PromptMessage(
        role="user",
        content=TextContent(
            type="text",
            text=(
                f"You are a Lead Infrastructure Reliability Engineer. "
                f"Evaluate the degraded state of cluster '{cluster_id}' and formulate a zero-downtime recovery runbook."
            )
        )
    )

    msg_telemetry = PromptMessage(
        role="user",
        content=EmbeddedResource(
            type="resource",
            resource=TextResourceContents(
                uri=f"k8s://clusters/{cluster_id}/status",
                mimeType="text/markdown",
                text=f"Status: {cluster_data['status']}\nCPU: {cluster_data['cpu_utilization'] * 100}%\nNodes: {cluster_data['nodes']}"
            )
        )
    )

    return [msg_instruction, msg_telemetry]


if __name__ == "__main__":
    mcp.run(transport="stdio")
