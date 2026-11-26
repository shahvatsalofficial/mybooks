from __future__ import annotations

import asyncio
from typing import Dict, List, Set
from pydantic import BaseModel


class AclMutationEvent(BaseModel):
    doc_id: str
    action: str  # "update_roles" | "revoke"
    new_roles: Set[str] = set()


class IncrementalAclSyncWorker:
    """Applies metadata-only ACL updates and tombstones without re-embedding."""

    def __init__(self, store: PreRetrievalVectorStore) -> None:
        self.store = store

    async def process_events(self, events: List[AclMutationEvent]) -> Dict[str, int]:
        await asyncio.sleep(0.005)
        updated_chunks = 0
        revoked_chunks = 0
        by_doc: Dict[str, AclMutationEvent] = {e.doc_id: e for e in events}

        for chunk in self.store._chunks:
            ev = by_doc.get(chunk.doc_id)
            if ev is None:
                continue
            if ev.action == "revoke":
                chunk.acl.is_revoked = True
                revoked_chunks += 1
            elif ev.action == "update_roles":
                chunk.acl.allowed_roles = set(ev.new_roles)
                updated_chunks += 1

        return {"updated_chunks": updated_chunks, "revoked_chunks": revoked_chunks}


async def demo_acl_sync() -> None:
    store = PreRetrievalVectorStore()
    store.upsert(VectorChunk(
        chunk_id="c10", doc_id="doc_audit_2026",
        text="HIPAA remediation checklist.",
        embedding=[0.7, 0.7, 0.0],
        acl=DocumentAcl(doc_id="doc_audit_2026", tenant_id="acme_corp", allowed_roles={"employee"}),
    ))
    worker = IncrementalAclSyncWorker(store)
    stats = await worker.process_events([
        AclMutationEvent(doc_id="doc_audit_2026", action="update_roles", new_roles={"sec_auditor"})
    ])
    print(f"Sync stats: {stats} | Updated roles: {store._chunks[0].acl.allowed_roles}")


if __name__ == "__main__":
    asyncio.run(demo_acl_sync())
