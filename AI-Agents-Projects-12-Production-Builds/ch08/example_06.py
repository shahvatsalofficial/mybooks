from __future__ import annotations

import asyncio
from typing import List
from pydantic import BaseModel, Field


class DiagramEdge(BaseModel):
    source: str
    target: str
    protocol: str = "HTTPS"
    crosses_trust_boundary: bool = False


class DiagramExtraction(BaseModel):
    doc_id: str
    page_number: int
    title: str
    components: List[str] = Field(default_factory=list)
    edges: List[DiagramEdge] = Field(default_factory=list)
    compliance_notes: str = ""

    def to_searchable_chunk(self) -> str:
        edge_lines = [
            f"{e.source} -> {e.target} ({e.protocol}, boundary_cross={e.crosses_trust_boundary})"
            for e in self.edges
        ]
        return (
            f"[DIAGRAM: {self.title} | Doc: {self.doc_id} p.{self.page_number}]\n"
            f"Components: {', '.join(self.components)}\n"
            f"Data Flows: {'; '.join(edge_lines)}\n"
            f"Compliance Notes: {self.compliance_notes}"
        )


class VisionDiagramExtractor:
    """Simulates Vision-LLM structured extraction of architecture diagrams."""

    async def extract_from_page(self, doc_id: str, page_number: int) -> DiagramExtraction:
        await asyncio.sleep(0.02)
        return DiagramExtraction(
            doc_id=doc_id,
            page_number=page_number,
            title="VPC Zero-Trust Payment Ingestion Topology",
            components=["Cloudflare WAF", "Kong API Gateway", "Tokenization Service", "RDS Postgres"],
            edges=[
                DiagramEdge(source="Cloudflare WAF", target="Kong API Gateway", protocol="mTLS", crosses_trust_boundary=True),
                DiagramEdge(source="Kong API Gateway", target="Tokenization Service", protocol="gRPC"),
                DiagramEdge(source="Tokenization Service", target="RDS Postgres", protocol="TLS 1.3"),
            ],
            compliance_notes="PCI-DSS cardholder data never leaves Tokenization Service unencrypted.",
        )


async def demo_diagram_extractor() -> None:
    ext = VisionDiagramExtractor()
    diag = await ext.extract_from_page("doc_pci_arch", 4)
    print(diag.to_searchable_chunk())


if __name__ == "__main__":
    asyncio.run(demo_diagram_extractor())
