from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from enum import Enum
from typing import Annotated
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator


class SourceTier(str, Enum):
    PRIMARY_OFFICIAL = "primary_official"
    PEER_REVIEWED = "peer_reviewed"
    ENGINEERING_BLOG = "engineering_blog"
    NEWS_AGGREGATOR = "news_aggregator"
    UNVERIFIED_FORUM = "unverified_forum"


class SubQueryNode(BaseModel):
    model_config = ConfigDict(frozen=True)

    node_id: str = Field(min_length=2, max_length=64)
    query_text: str = Field(min_length=5, max_length=300)
    target_tiers: list[SourceTier] = Field(min_length=1)
    depends_on: list[str] = Field(default_factory=list)
    max_results: int = Field(default=6, ge=1, le=20)
    wave_index: int = Field(default=0, ge=0, le=5)


class ResearchDAG(BaseModel):
    root_objective: str = Field(min_length=10, max_length=500)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    nodes: list[SubQueryNode] = Field(min_length=1, max_length=24)

    @field_validator("nodes")
    @classmethod
    def validate_acyclic_dependencies(cls, nodes: list[SubQueryNode]) -> list[SubQueryNode]:
        known_ids = {n.node_id for n in nodes}
        for node in nodes:
            unknown = set(node.depends_on) - known_ids
            if unknown:
                raise ValueError(f"Node {node.node_id} references unknown dependencies: {unknown}")
        # Kahn's algorithm cycle check
        in_degree: dict[str, int] = {n.node_id: len(n.depends_on) for n in nodes}
        adj: dict[str, list[str]] = {n.node_id: [] for n in nodes}
        for n in nodes:
            for dep in n.depends_on:
                adj[dep].append(n.node_id)
        queue = [nid for nid, deg in in_degree.items() if deg == 0]
        visited = 0
        while queue:
            curr = queue.pop(0)
            visited += 1
            for nxt in adj[curr]:
                in_degree[nxt] -= 1
                if in_degree[nxt] == 0:
                    queue.append(nxt)
        if visited != len(nodes):
            raise ValueError("Cycle detected in ResearchDAG node dependencies")
        return nodes


class SourceDocument(BaseModel):
    model_config = ConfigDict(frozen=True)

    doc_id: str = Field(default_factory=lambda: f"doc_{uuid4().hex[:12]}")
    url: HttpUrl
    domain: str = Field(min_length=3)
    title: str = Field(min_length=1, max_length=400)
    raw_text: str = Field(min_length=50)
    published_at: datetime | None = None
    retrieved_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    tier: SourceTier = SourceTier.NEWS_AGGREGATOR
    content_sha256: str = ""
    trust_score: Annotated[float, Field(ge=0.0, le=1.0)] = 0.5

    @field_validator("content_sha256", mode="before")
    @classmethod
    def compute_sha256(cls, v: str, info) -> str:
        if v:
            return v
        raw = info.data.get("raw_text", "")
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()


class EvidenceSpan(BaseModel):
    model_config = ConfigDict(frozen=True)

    span_id: str
    doc_id: str
    url: HttpUrl
    start_char: int = Field(ge=0)
    end_char: int = Field(gt=0)
    exact_quote: str = Field(min_length=15, max_length=1200)


class AtomicClaim(BaseModel):
    claim_id: str
    statement: str = Field(min_length=15, max_length=600)
    supporting_span_ids: list[str] = Field(min_length=1)
    entailment_score: float = Field(default=0.0, ge=0.0, le=1.0)
    verified: bool = False


if __name__ == "__main__":
    dag = ResearchDAG(
        root_objective="Evaluate 2026 zero-knowledge rollup verifier costs and audit status",
        nodes=[
            SubQueryNode(
                node_id="q1_specs",
                query_text="ZK rollup verifier gas cost benchmarks 2026 official docs",
                target_tiers=[SourceTier.PRIMARY_OFFICIAL, SourceTier.ENGINEERING_BLOG],
                wave_index=0,
            ),
            SubQueryNode(
                node_id="q2_audits",
                query_text="ZK rollup security audit reports CVE 2025 2026",
                target_tiers=[SourceTier.PRIMARY_OFFICIAL, SourceTier.PEER_REVIEWED],
                wave_index=0,
            ),
            SubQueryNode(
                node_id="q3_synthesis_gap",
                query_text="Compare prover hardware cost against verifier L1 settlement fee",
                target_tiers=[SourceTier.ENGINEERING_BLOG, SourceTier.PEER_REVIEWED],
                depends_on=["q1_specs", "q2_audits"],
                wave_index=1,
            ),
        ],
    )
    doc = SourceDocument(
        url="https://docs.example-zk.org/benchmarks/2026",
        domain="docs.example-zk.org",
        title="2026 Verifier Gas Benchmarks",
        raw_text="The Groth16 on-chain verifier consumes 218,400 gas per batch proof on Ethereum mainnet.",
        tier=SourceTier.PRIMARY_OFFICIAL,
        trust_score=0.94,
    )
    print(f"DAG validated: {len(dag.nodes)} nodes, root='{dag.root_objective[:42]}...'")
    print(f"Doc={doc.doc_id} sha256={doc.content_sha256[:16]}... trust={doc.trust_score}")
