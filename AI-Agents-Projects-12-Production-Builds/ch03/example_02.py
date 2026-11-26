from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple
from pydantic import BaseModel


class DeduplicationResult(BaseModel):
    is_duplicate: bool
    master_ticket_id: str
    similarity_score: float
    merged_channels: List[str]


@dataclass
class ActiveThreadEntry:
    master_ticket_id: str
    tenant_id: str
    tokens: Set[str]
    channels: List[str] = field(default_factory=list)
    created_epoch: float = field(default_factory=time.time)


class ThreadDeduplicator:
    """Merges cross-channel duplicate tickets for the same tenant within a TTL."""

    def __init__(self, window_seconds: int = 900, threshold: float = 0.45) -> None:
        self._window = window_seconds
        self._threshold = threshold
        self._threads: Dict[str, List[ActiveThreadEntry]] = {}

    @staticmethod
    def _tokenize(text: str) -> Set[str]:
        words = {w.strip(".,!?:;\"'()").lower() for w in text.split()}
        return {w for w in words if len(w) > 2}

    @staticmethod
    def _jaccard(a: Set[str], b: Set[str]) -> float:
        if not a or not b:
            return 0.0
        return len(a & b) / len(a | b)

    def evaluate(
        self, ticket_id: str, tenant_id: str, channel: str, text: str
    ) -> DeduplicationResult:
        now = time.time()
        entries = self._threads.setdefault(tenant_id, [])
        entries[:] = [e for e in entries if (now - e.created_epoch) <= self._window]

        tokens = self._tokenize(text)
        best_entry: Optional[ActiveThreadEntry] = None
        best_score = 0.0

        for entry in entries:
            score = self._jaccard(tokens, entry.tokens)
            if score > best_score:
                best_score = score
                best_entry = entry

        if best_entry is not None and best_score >= self._threshold:
            if channel not in best_entry.channels:
                best_entry.channels.append(channel)
            return DeduplicationResult(
                is_duplicate=True,
                master_ticket_id=best_entry.master_ticket_id,
                similarity_score=round(best_score, 3),
                merged_channels=list(best_entry.channels),
            )

        new_entry = ActiveThreadEntry(
            master_ticket_id=ticket_id,
            tenant_id=tenant_id,
            tokens=tokens,
            channels=[channel],
        )
        entries.append(new_entry)
        return DeduplicationResult(
            is_duplicate=False,
            master_ticket_id=ticket_id,
            similarity_score=0.0,
            merged_channels=[channel],
        )


if __name__ == "__main__":
    dedup = ThreadDeduplicator(window_seconds=900, threshold=0.40)
    r1 = dedup.evaluate(
        "TKT-A49E1C7B2D",
        "ten_acme_01",
        "zendesk",
        "Production payouts are failing with 502 Bad Gateway errors since 06:40 UTC",
    )
    r2 = dedup.evaluate(
        "TKT-F91C02B811",
        "ten_acme_01",
        "slack",
        "Hey team our production payouts are failing with 502 Bad Gateway right now",
    )
    print("First ticket:", r1.model_dump())
    print("Second ticket:", r2.model_dump())
