class StateEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = Field(default_factory=time.time)
    event_type: str
    delta_payload: Dict[str, Any]

class EventSourcedAgentState:
    def __init__(self, initial_state: Dict[str, Any]):
        self._events: List[StateEvent] = []
        self._snapshot = initial_state

    def apply_event(self, event_type: str, delta: Dict[str, Any]):
        evt = StateEvent(event_type=event_type, delta_payload=delta)
        self._events.append(evt)
        self._snapshot.update(delta)
        print(f"[EVENT SOURCING] Applied '{event_type}' (Total Events: {len(self._events)})")

    def reconstruct_state_at(self, target_timestamp: float) -> Dict[str, Any]:
        replay = {}
        for evt in self._events:
            if evt.timestamp <= target_timestamp:
                replay.update(evt.delta_payload)
        return replay
