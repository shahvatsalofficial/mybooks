from __future__ import annotations

import asyncio
import math
from typing import Any, Dict, List
from pydantic import BaseModel, Field


class VectorChunk(BaseModel):
    chunk_id: str
    doc_id: str
    text: str
    embedding: List[float]
    acl: DocumentAcl


class PreFilterSearchResult(BaseModel):
    chunk_id: str
    doc_id: str
    score: float
    text: str


class PreRetrievalVectorStore:
    """In-memory vector store enforcing pre-retrieval ACL predicates."""

    def __init__(self) -> None:
        self._chunks: List[VectorChunk] = []

    def upsert(self, chunk: VectorChunk) -> None:
        self._chunks.append(chunk)

    @staticmethod
    def _cosine(a: List[float], b: List[float]) -> float:
        dot = sum(x * y for x, y in zip(a, b))
        na = math.sqrt(sum(x * x for x in a))
        nb = math.sqrt(sum(y * y for y in b))
        return dot / (na * nb) if na and nb else 0.0

    @staticmethod
    def _matches_acl(principal: PrincipalContext, acl: DocumentAcl) -> bool:
        if acl.is_revoked or acl.tenant_id != principal.tenant_id:
            return False
        if principal.clearance < acl.min_clearance:
            return False
        if principal.user_id in acl.allowed_users:
            return True
        return len(principal.roles & acl.allowed_roles) > 0

    async def search(
        self, principal: PrincipalContext, query_vec: List[float], top_k: int = 3
    ) -> List[PreFilterSearchResult]:
        await asyncio.sleep(0.006)
        authorized = [c for c in self._chunks if self._matches_acl(principal, c.acl)]
        scored = [
            PreFilterSearchResult(
                chunk_id=c.chunk_id,
                doc_id=c.doc_id,
                score=round(self._cosine(query_vec, c.embedding), 4),
                text=c.text,
            )
            for c in authorized
        ]
        scored.sort(key=lambda r: r.score, reverse=True)
        return scored[:top_k]


async def demo_prefilter_search() -> None:
    store = PreRetrievalVectorStore()
    store.upsert(VectorChunk(
        chunk_id="c1", doc_id="doc_hr_bonus",
        text="Q4 Executive Retention Bonus: $450,000 VP tier.",
        embedding=[0.9, 0.1, 0.0],
        acl=DocumentAcl(doc_id="doc_hr_bonus", tenant_id="acme_corp", allowed_roles={"hr_exec"}, min_clearance=ClearanceLevel.RESTRICTED),
    ))
    store.upsert(VectorChunk(
        chunk_id="c2", doc_id="doc_eng_runbook",
        text="SOC2 encryption key rotation runbook for platform services.",
        embedding=[0.85, 0.2, 0.0],
        acl=DocumentAcl(doc_id="doc_eng_runbook", tenant_id="acme_corp", allowed_roles={"engineer"}, min_clearance=ClearanceLevel.INTERNAL),
    ))

    contractor = PrincipalContext(
        user_id="u_ext_9", tenant_id="acme_corp", roles={"external_support"},
        department="support", clearance=ClearanceLevel.INTERNAL, exp_epoch=9999999999,
    )
    engineer = PrincipalContext(
        user_id="u_8841", tenant_id="acme_corp", roles={"engineer"},
        department="platform", clearance=ClearanceLevel.INTERNAL, exp_epoch=9999999999,
    )
    q = [0.88, 0.15, 0.0]
    res_ext = await store.search(contractor, q, top_k=3)
    res_eng = await store.search(engineer, q, top_k=3)
    print(f"Contractor hits: {[r.doc_id for r in res_ext]}")
    print(f"Engineer hits: {[r.doc_id for r in res_eng]}")


if __name__ == "__main__":
    asyncio.run(demo_prefilter_search())
