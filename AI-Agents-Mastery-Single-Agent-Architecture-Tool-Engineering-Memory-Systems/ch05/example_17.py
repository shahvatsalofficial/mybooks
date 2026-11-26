import json
import time
from typing import Dict, Any, List

class SimulatedAMQPExchange:
    def __init__(self, exchange_name: str):
        self.exchange_name = exchange_name
        self.queues: Dict[str, List[str]] = {}

    def declare_queue(self, queue_name: str, routing_key: str) -> None:
        self.queues[routing_key] = []
        print(f"[AMQP] Bound queue '{queue_name}' to exchange '{self.exchange_name}' with key '{routing_key}'")

    def publish_message(self, routing_key: str, message_payload: Dict[str, Any]) -> None:
        payload_str = json.dumps(message_payload)
        if routing_key in self.queues:
            self.queues[routing_key].append(payload_str)
            print(f"[AMQP] Published message to '{routing_key}' (Payload size: {len(payload_str)} bytes)")
        else:
            print(f"[AMQP WARNING] Unroutable message for key: '{routing_key}'")

    def consume_message(self, routing_key: str) -> Dict[str, Any]:
        if routing_key in self.queues and self.queues[routing_key]:
            raw = self.queues[routing_key].pop(0)
            return json.loads(raw)
        return {}

exchange = SimulatedAMQPExchange("agent.events")
exchange.declare_queue("q.audit.tasks", "audit.financial.*")
exchange.publish_message("audit.financial.*", {"task_id": "TSK-992", "account": "ACC-1002", "amount": 8500})
msg = exchange.consume_message("audit.financial.*")
print("Consumer Agent Ingested Message:", msg["task_id"])
