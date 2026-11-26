from __future__ import annotations

from typing import List


def verify_tenant_isolation(chunks: List[VectorChunk], expected_tenant: str) -> bool:
    return all(c.acl.tenant_id == expected_tenant for c in chunks)


if __name__ == "__main__":
    sample = [
        VectorChunk(
            chunk_id="c1", doc_id="d1", text="ok", embedding=[1.0, 0.0],
            acl=DocumentAcl(doc_id="d1", tenant_id="acme_corp", allowed_roles={"employee"}),
        )
    ]
    print("Isolated:", verify_tenant_isolation(sample, "acme_corp"))
