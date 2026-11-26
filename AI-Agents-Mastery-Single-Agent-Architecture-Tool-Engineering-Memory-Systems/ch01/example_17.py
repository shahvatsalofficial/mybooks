import time
from typing import List, Literal, Any
from pydantic import BaseModel, Field

class AgentLifecycleEvent(BaseModel):
    event_id: str
    timestamp: float = Field(default_factory=time.time)
    event_type: Literal["THINKING_START", "TOOL_CALLED", "OBSERVATION_INGESTED", "TURN_COMPLETE"]
    payload: dict[str, Any]

class ImmutableEventJournal:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.events: List[AgentLifecycleEvent] = []

    def record_event(self, event_type: str, payload: dict[str, Any]) -> AgentLifecycleEvent:
        evt = AgentLifecycleEvent(
            event_id=f"EVT-{len(self.events) + 1:04d}",
            event_type=event_type,
            payload=payload
        )
        self.events.append(evt)
        print(f"[AUDIT JOURNAL] Recorded {evt.event_type} -> ID: {evt.event_id}")
        return evt

    def dump_audit_trail(self) -> List[dict[str, Any]]:
        return [e.model_dump() for e in self.events]

journal = ImmutableEventJournal("SESS-FIN-881")
journal.record_event("THINKING_START", {"query": "Execute wire transfer"})
journal.record_event("TOOL_CALLED", {"tool": "bank_api", "amount": 5000})
journal.record_event("TURN_COMPLETE", {"status": "SUCCESS"})
