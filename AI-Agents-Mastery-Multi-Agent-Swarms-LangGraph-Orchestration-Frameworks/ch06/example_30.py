from typing import Dict, Any, Optional
from pydantic import BaseModel

class AMQPDeadLetterTopologyConfig(BaseModel):
    main_exchange: str = "agent.tasks.direct"
    retry_exchange: str = "agent.tasks.retry"
    dlx_exchange: str = "agent.tasks.deadletter"
    main_queue: str = "agent_execution_queue"
    retry_delay_ms: int = 5000 # 5-second backoff delay
    max_retry_attempts: int = 3

class EnterpriseAMQPDeadLetterManager:
    """Configures AMQP exchange bindings for delayed retries and dead-letter parking."""
    
    def __init__(self, config: AMQPDeadLetterTopologyConfig):
        self.cfg = config
        self.dlq_messages: List[Dict[str, Any]] = []

    def declare_amqp_arguments(self) -> Dict[str, Any]:
        """Returns standard RabbitMQ queue declaration arguments for retry & DLX."""
        return {
            # Route rejected or expired messages to retry exchange
            "x-dead-letter-exchange": self.cfg.retry_exchange,
            "x-dead-letter-routing-key": "retry.step",
            "x-max-priority": 10
        }

    def declare_delayed_retry_queue_args(self) -> Dict[str, Any]:
        """Delayed queue holds messages for TTL duration before dead-lettering back to main queue."""
        return {
            "x-dead-letter-exchange": self.cfg.main_exchange,
            "x-dead-letter-routing-key": "execute.step",
            "x-message-ttl": self.cfg.retry_delay_ms # Message automatically re-enters main queue after 5s
        }

    def route_to_poison_dlq(self, message_id: str, error_reason: str, body: Dict[str, Any]) -> None:
        record = {
            "message_id": message_id,
            "error_reason": error_reason,
            "failed_at": time.time(),
            "payload": body
        }
        self.dlq_messages.append(record)
        print(f"[DLQ PARK] Permanent failure on {message_id}: {error_reason}. Parked in Dead-Letter Queue.")
