from __future__ import annotations

from datetime import datetime, timedelta, timezone
from enum import Enum
from pydantic import BaseModel, Field


class SequenceState(str, Enum):
    ACTIVE_TOUCH_1 = "active_touch_1"
    ACTIVE_TOUCH_2 = "active_touch_2"
    ACTIVE_TOUCH_3 = "active_touch_3"
    ESCALATED_TO_AE = "escalated_to_ae"
    HALTED_REPLY = "halted_reply"
    HALTED_BOUNCE = "halted_bounce"
    COMPLETED_NO_REPLY = "completed_no_reply"


class SequenceRecord(BaseModel):
    lead_id: str
    routing_tier: str
    state: SequenceState = SequenceState.ACTIVE_TOUCH_1
    touch_count: int = Field(default=1, ge=0)
    pricing_clicks_24h: int = Field(default=0, ge=0)
    next_send_utc: datetime


def advance_sequence_state(
    rec: SequenceRecord,
    event_type: str,
    now_utc: datetime,
) -> SequenceRecord:
    if event_type in {"reply_positive", "reply_unsubscribe", "reply_objection"}:
        return rec.model_copy(update={"state": SequenceState.HALTED_REPLY})
    if event_type == "hard_bounce":
        return rec.model_copy(update={"state": SequenceState.HALTED_BOUNCE})
    if event_type == "pricing_link_click":
        clicks = rec.pricing_clicks_24h + 1
        if clicks >= 2 and rec.routing_tier == "tier_a_ae_fast_track":
            return rec.model_copy(update={"pricing_clicks_24h": clicks, "state": SequenceState.ESCALATED_TO_AE})
        return rec.model_copy(update={"pricing_clicks_24h": clicks})

    if event_type == "cadence_timer_elapsed":
        if rec.state == SequenceState.ACTIVE_TOUCH_1:
            return rec.model_copy(
                update={
                    "state": SequenceState.ACTIVE_TOUCH_2,
                    "touch_count": 2,
                    "next_send_utc": now_utc + timedelta(days=3),
                }
            )
        if rec.state == SequenceState.ACTIVE_TOUCH_2:
            return rec.model_copy(
                update={
                    "state": SequenceState.ACTIVE_TOUCH_3,
                    "touch_count": 3,
                    "next_send_utc": now_utc + timedelta(days=4),
                }
            )
        return rec.model_copy(update={"state": SequenceState.COMPLETED_NO_REPLY})

    return rec


if __name__ == "__main__":
    now = datetime(2026, 11, 25, 14, 0, tzinfo=timezone.utc)
    seq = SequenceRecord(
        lead_id="LD-88412",
        routing_tier="tier_a_ae_fast_track",
        next_send_utc=now + timedelta(days=2),
    )
    seq = advance_sequence_state(seq, "cadence_timer_elapsed", now)
    print("After timer:", seq.state.value, "touch=", seq.touch_count)
    seq = advance_sequence_state(seq, "pricing_link_click", now)
    seq = advance_sequence_state(seq, "pricing_link_click", now)
    print("After 2 pricing clicks:", seq.state.value, "clicks=", seq.pricing_clicks_24h)
