from __future__ import annotations

from collections import defaultdict
from typing import Dict, List, Tuple
from pydantic import BaseModel


class RankedChunk(BaseModel):
    chunk_id: str
    cik: str
    is_superseded: bool
    rrf_score: float
    text: str


class HybridFinancialRetriever:
    """Fuses lexical and dense rankings using Reciprocal Rank Fusion (RRF)."""

    @staticmethod
    def fuse_rrf(
        target_cik: str,
        lexical_ranked: List[Tuple[str, str, bool, str]],
        dense_ranked: List[Tuple[str, str, bool, str]],
        k: int = 60,
        top_n: int = 3,
    ) -> List[RankedChunk]:
        scores: Dict[str, float] = defaultdict(float)
        payloads: Dict[str, Tuple[str, bool, str]] = {}

        for rank, (cid, cik, superseded, text) in enumerate(lexical_ranked, start=1):
            if cik != target_cik or superseded:
                continue
            scores[cid] += 1.0 / (k + rank)
            payloads[cid] = (cik, superseded, text)

        for rank, (cid, cik, superseded, text) in enumerate(dense_ranked, start=1):
            if cik != target_cik or superseded:
                continue
            scores[cid] += 1.0 / (k + rank)
            payloads[cid] = (cik, superseded, text)

        ordered = sorted(scores.items(), key=lambda item: item[1], reverse=True)[:top_n]
        return [
            RankedChunk(
                chunk_id=cid,
                cik=payloads[cid][0],
                is_superseded=payloads[cid][1],
                rrf_score=round(score, 6),
                text=payloads[cid][2],
            )
            for cid, score in ordered
        ]


if __name__ == "__main__":
    lex = [
        ("c1", "0000950170", False, "Leverage covenant max 3.50x EBITDA under 2025 credit facility."),
        ("c2", "0000950170", True, "Superseded 2024 covenant draft."),
    ]
    dense = [
        ("c3", "0000999999", False, "Competitor debt schedule."),
        ("c1", "0000950170", False, "Leverage covenant max 3.50x EBITDA under 2025 credit facility."),
    ]
    hits = HybridFinancialRetriever.fuse_rrf("0000950170", lex, dense)
    for h in hits:
        print(h.model_dump())
