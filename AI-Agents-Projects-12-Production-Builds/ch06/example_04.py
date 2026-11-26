from __future__ import annotations

import math
from datetime import datetime, timezone
from pydantic import BaseModel, Field


class IntentSignal(BaseModel):
    signal_type: str
    base_weight: float = Field(gt=0.0)
    half_life_days: float = Field(gt=0.0)
    occurred_at: datetime


def compute_decayed_intent_score(signals: list[IntentSignal], reference_time: datetime) -> float:
    if reference_time.tzinfo is None:
        reference_time = reference_time.replace(tzinfo=timezone.utc)

    total = 0.0
    for sig in signals:
        ts = sig.occurred_at.replace(tzinfo=timezone.utc) if sig.occurred_at.tzinfo is None else sig.occurred_at
        age_days = max(0.0, (reference_time - ts).total_seconds() / 86_400.0)
        decay_factor = math.pow(0.5, age_days / sig.half_life_days)
        total += sig.base_weight * decay_factor
    return round(min(100.0, total), 2)


if __name__ == "__main__":
    now = datetime(2026, 11, 25, 14, 0, 0, tzinfo=timezone.utc)
    events = [
        IntentSignal(signal_type="pricing_page_visit", base_weight=35.0, half_life_days=7.0, occurred_at=datetime(2026, 11, 25, 13, 30, tzinfo=timezone.utc)),
        IntentSignal(signal_type="api_docs_quickstart", base_weight=25.0, half_life_days=14.0, occurred_at=datetime(2026, 11, 22, 14, 0, tzinfo=timezone.utc)),
        IntentSignal(signal_type="webinar_attended", base_weight=20.0, half_life_days=10.0, occurred_at=datetime(2026, 10, 10, 14, 0, tzinfo=timezone.utc)),
    ]
    print("Decayed Intent Score:", compute_decayed_intent_score(events, now))
