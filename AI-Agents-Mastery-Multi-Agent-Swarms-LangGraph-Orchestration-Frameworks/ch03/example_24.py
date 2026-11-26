import json
import time
import uuid
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

class OutboxEventMessage(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: str
    aggregate_thread_id: str
    payload: Dict[str, Any]
    created_at: float = Field(default_factory=time.time)
    dispatched_to_broker: bool = False

class SubgraphTransactionalOutboxRelay:
    """Safely stages and asynchronously flushes events to external message brokers."""
    
    def __init__(self, broker_topic: str = "swarm.subgraph.events"):
        self.broker_topic = broker_topic
        self.in_flight_outbox: List[OutboxEventMessage] = []
        self.dispatched_ledger: List[str] = []

    def stage_event(self, event_type: str, thread_id: str, payload: Dict[str, Any]) -> OutboxEventMessage:
        msg = OutboxEventMessage(
            event_type=event_type,
            aggregate_thread_id=thread_id,
            payload=payload
        )
        self.in_flight_outbox.append(msg)
        print(f"[OUTBOX STAGE] Event staged: {event_type} ({msg.event_id[:8]}) for thread '{thread_id}'.")
        return msg

    def flush_outbox_to_stream(self, simulated_broker_success: bool = True) -> int:
        flushed_count = 0
        for msg in list(self.in_flight_outbox):
            if simulated_broker_success:
                msg.dispatched_to_broker = True
                self.dispatched_ledger.append(msg.event_id)
                self.in_flight_outbox.remove(msg)
                flushed_count += 1
                print(f"[BROKER PUBLISH] Successfully pushed event {msg.event_id[:8]} to topic '{self.broker_topic}'.")
            else:
                print(f"[BROKER ERROR] Delivery failed for {msg.event_id[:8]}! Event retained in outbox for retry.")
        return flushed_count
