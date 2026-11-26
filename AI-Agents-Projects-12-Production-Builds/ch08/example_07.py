from __future__ import annotations

from typing import Dict, List
from pydantic import BaseModel


class NormalizedTableChunk(BaseModel):
    doc_id: str
    table_title: str
    row_index: int
    record: Dict[str, str]
    rendered_text: str


class ComplianceTableNormalizer:
    """Normalizes extracted table matrices into header-preserving searchable chunks."""

    def normalize(
        self, doc_id: str, table_title: str, headers: List[str], rows: List[List[str]]
    ) -> List[NormalizedTableChunk]:
        chunks: List[NormalizedTableChunk] = []
        for idx, row in enumerate(rows):
            padded = row + [""] * (len(headers) - len(row))
            rec = {h: val.strip() for h, val in zip(headers, padded)}
            kv_pairs = " | ".join(f"{k}: {v}" for k, v in rec.items())
            chunks.append(
                NormalizedTableChunk(
                    doc_id=doc_id,
                    table_title=table_title,
                    row_index=idx,
                    record=rec,
                    rendered_text=f"[{table_title} | {doc_id}] {kv_pairs}",
                )
            )
        return chunks


def demo_table_normalizer() -> None:
    norm = ComplianceTableNormalizer()
    chunks = norm.normalize(
        doc_id="doc_sla_matrix",
        table_title="HIPAA & SOC2 Retention Schedule",
        headers=["Data Class", "Retention", "Encryption", "Owner"],
        rows=[
            ["Audit Logs", "7 Years", "AES-256-GCM", "SecOps"],
            ["Support Transcripts", "90 Days", "AES-256", "Support Engineering"],
        ],
    )
    for c in chunks:
        print(c.rendered_text)


if __name__ == "__main__":
    demo_table_normalizer()
