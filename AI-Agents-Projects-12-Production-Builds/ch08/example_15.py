from __future__ import annotations

import asyncio
import time
from typing import List, Set
from pydantic import BaseModel, Field


class CompliantAnswer(BaseModel):
    answer_text: str
    cited_doc_ids: List[str] = Field(default_factory=list)
    pii_redacted_count: int
    blocked: bool
    latency_ms: float


class EnterpriseComplianceAgent:
    """Production RAG assistant with pre-retrieval ACLs and bidirectional shields."""

    def __init__(self, store: PreRetrievalVectorStore) -> None:
        self.store = store
        self.pii_scanner = BidirectionalPiiScanner()
        self.injection_shield = IndirectInjectionShield()
        self.citation_verifier = CitationGroundingVerifier()
        self.audit_logger = ImmutableAuditLogger()

    async def answer(
        self, principal: PrincipalContext, raw_query: str, query_vec: List[float]
    ) -> CompliantAnswer:
        t0 = time.perf_counter()

        # 1. Ingress PII scrub
        ingress_scan = self.pii_scanner.scan_and_redact(raw_query)
        safe_query = ingress_scan.redacted_text

        # 2. Pre-retrieval ACL-enforced vector search
        hits = await self.store.search(principal, query_vec, top_k=5)
        if not hits:
            self.audit_logger.record(principal, raw_query, [], len(ingress_scan.findings))
            return CompliantAnswer(
                answer_text="No authorized documents matched your query.",
                cited_doc_ids=[],
                pii_redacted_count=len(ingress_scan.findings),
                blocked=False,
                latency_ms=round((time.perf_counter() - t0) * 1000, 2),
            )

        # 3. Indirect prompt-injection inspection on retrieved chunks
        inj = self.injection_shield.inspect_texts([safe_query] + [h.text for h in hits])
        if not inj.is_safe:
            self.audit_logger.record(
                principal, raw_query, [h.doc_id for h in hits],
                len(ingress_scan.findings), blocked=True,
                reason=f"Injection blocked: {inj.matched_patterns}",
            )
            return CompliantAnswer(
                answer_text="Request blocked by policy enforcement shield.",
                cited_doc_ids=[],
                pii_redacted_count=len(ingress_scan.findings),
                blocked=True,
                latency_ms=round((time.perf_counter() - t0) * 1000, 2),
            )

        # 4. Synthesize grounded response + egress PII scrub + citation audit
        authorized_ids: Set[str] = {h.doc_id for h in hits}
        draft = f"Based on policy guidance: {hits[0].text} [{hits[0].doc_id}]."
        egress_scan = self.pii_scanner.scan_and_redact(draft)
        cite_audit = self.citation_verifier.verify(egress_scan.redacted_text, authorized_ids)
        total_pii = len(ingress_scan.findings) + len(egress_scan.findings)

        self.audit_logger.record(principal, raw_query, list(authorized_ids), total_pii)
        return CompliantAnswer(
            answer_text=egress_scan.redacted_text if cite_audit.is_grounded else "Citation verification failed.",
            cited_doc_ids=cite_audit.cited_doc_ids,
            pii_redacted_count=total_pii,
            blocked=not cite_audit.is_grounded,
            latency_ms=round((time.perf_counter() - t0) * 1000, 2),
        )


async def demo_ci_gate() -> None:
    store = PreRetrievalVectorStore()
    store.upsert(VectorChunk(
        chunk_id="c1", doc_id="doc_hr_bonus",
        text="Q4 Executive Retention Bonus: $450,000 VP tier.",
        embedding=[0.9, 0.1, 0.0],
        acl=DocumentAcl(doc_id="doc_hr_bonus", tenant_id="acme_corp", allowed_roles={"hr_exec"}, min_clearance=ClearanceLevel.RESTRICTED),
    ))
    store.upsert(VectorChunk(
        chunk_id="c2", doc_id="doc_eng_runbook",
        text="Rotate KMS keys quarterly; contact secops@acme.com.",
        embedding=[0.85, 0.2, 0.0],
        acl=DocumentAcl(doc_id="doc_eng_runbook", tenant_id="acme_corp", allowed_roles={"engineer"}, min_clearance=ClearanceLevel.INTERNAL),
    ))

    agent = EnterpriseComplianceAgent(store)
    suite = build_golden_eval_suite()
    retrieved_sets: List[Set[str]] = []
    responses: List[str] = []

    for case in suite:
        p = PrincipalContext(
            user_id="ci_probe", tenant_id="acme_corp",
            roles=case.principal_roles, department="ci",
            clearance=case.clearance, exp_epoch=9999999999,
        )
        ans = await agent.answer(p, case.query, [0.87, 0.15, 0.0])
        retrieved_sets.append(set(ans.cited_doc_ids))
        responses.append(ans.answer_text)

    metrics = ComplianceEvalScorer(min_recall=0.90).score_batch(suite, retrieved_sets, responses)
    print(f"CI Release Gate Passed: {metrics.passed_ci_gate} | Recall@5: {metrics.recall_at_k} | ACL Leaks: {metrics.acl_leak_count} | PII Escapes: {metrics.pii_escape_count}")


if __name__ == "__main__":
    asyncio.run(demo_ci_gate())
