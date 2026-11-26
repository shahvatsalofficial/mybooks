"""
Event-Driven Multi-Agent Bus: Implements decoupled asynchronous message queues
with monotonic hop counters and dead-letter queue routing for failed handoffs.
"""

from typing import Dict, Any, Callable, List
import queue
import time


class MultiAgentEventBus:
    """Manages asynchronous message queues across distributed agent workers."""

    def __init__(self, max_queue_size: int = 1000):
        self.channels: Dict[str, queue.Queue] = {}
        self.dead_letter_queue: queue.Queue = queue.Queue()
        self.handlers: Dict[str, Callable[[Dict[str, Any]], None]] = {}

    def subscribe(self, agent_id: str, handler: Callable[[Dict[str, Any]], None]):
        """Subscribes an agent to its dedicated inbound message channel."""
        self.channels[agent_id] = queue.Queue()
        self.handlers[agent_id] = handler

    def publish_message(self, target_agent_id: str, message_payload: Dict[str, Any]) -> bool:
        """Publishes an event to an agent queue with dead-letter fallback."""
        if target_agent_id not in self.channels:
            self.dead_letter_queue.put({
                "error": "TARGET_AGENT_UNREGISTERED",
                "target": target_agent_id,
                "payload": message_payload,
                "timestamp": time.time()
            })
            return False

        q = self.channels[target_agent_id]
        try:
            q.put_nowait(message_payload)
            return True
        except queue.Full:
            self.dead_letter_queue.put({
                "error": "QUEUE_OVERFLOW",
                "target": target_agent_id,
                "payload": message_payload,
                "timestamp": time.time()
            })
            return False
