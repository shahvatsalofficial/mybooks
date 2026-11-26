from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, List
from pydantic import BaseModel


class SourceFreshnessStatus(BaseModel):
    source_id: str
    age_minutes: float
    is_fresh: bool


def evaluate_source_freshness(
    source_loaded_at_iso: Dict[str, str],
    now_utc: datetime,
    max_staleness_minutes: float = 60.0,
) -> List[SourceFreshnessStatus]:
    results: List[SourceFreshnessStatus] = []
    for src_id, iso_ts in source_loaded_at_iso.items():
        loaded = datetime.fromisoformat(iso_ts.replace("Z", "+00:00"))
        age_min = (now_utc - loaded).total_seconds() / 60.0
        results.append(
            SourceFreshnessStatus(
                source_id=src_id,
                age_minutes=round(age_min, 2),
                is_fresh=age_min <= max_staleness_minutes,
            )
        )
    return results


if __name__ == "__main__":
    now = datetime(2026, 8, 20, 3, 0, 0, tzinfo=timezone.utc)
    statuses = evaluate_source_freshness(
        {
            "source.fintech.raw_card_events": "2026-08-20T02:35:00Z",
            "source.fintech.raw_fx_rates": "2026-08-20T00:45:00Z",
        },
        now_utc=now,
    )
    for st in statuses:
        print(st.model_dump())
