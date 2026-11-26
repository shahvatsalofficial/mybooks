from __future__ import annotations

from collections import defaultdict
from typing import Dict, List, Tuple
from pydantic import BaseModel


class FusedRetrievalHit(BaseModel):
    doc_id: str
    rrf_score: float


def reciprocal_rank_fusion(
    ranked_lists: List[List[str]], k: int = 60, top_n: int = 5
) -> List[FusedRetrievalHit]:
    """Combines dense, diagram, and lexical rankings via Reciprocal Rank Fusion."""
    scores: Dict[str, float] = defaultdict(float)
    for rlist in ranked_lists:
        for rank, doc_id in enumerate(rlist, start=1):
            scores[doc_id] += 1.0 / (k + rank)

    ordered: List[Tuple[str, float]] = sorted(
        scores.items(), key=lambda item: item[1], reverse=True
    )
    return [
        FusedRetrievalHit(doc_id=doc_id, rrf_score=round(sc, 6))
        for doc_id, sc in ordered[:top_n]
    ]


def demo_rrf() -> None:
    dense_hits = ["doc_eng_runbook", "doc_pci_arch", "doc_sla_matrix"]
    diagram_hits = ["doc_pci_arch", "doc_vpc_peering"]
    bm25_hits = ["doc_pci_arch", "doc_sla_matrix", "doc_eng_runbook"]
    fused = reciprocal_rank_fusion([dense_hits, diagram_hits, bm25_hits], top_n=3)
    for hit in fused:
        print(f"{hit.doc_id}: rrf_score={hit.rrf_score}")


if __name__ == "__main__":
    demo_rrf()
