import json
from typing import Dict, Any, Callable
from pydantic import ValidationError

class KafkaMessagePayload(BaseModel):
    transaction_id: str
    raw_llm_payload: str
    retry_count: int = 0

class ResilientKafkaConsumer:
    def __init__(self, dlq_producer: Any, max_retries: int = 3):
        self.dlq_producer = dlq_producer
        self.max_retries = max_retries

    def consume_message(self, raw_record: str, schema_cls: type[BaseModel], process_fn: Callable[[BaseModel], None]):
        try:
            # 1. Parse outer record
            msg = KafkaMessagePayload.model_validate_json(raw_record)
            
            # 2. Deterministic sanitization & schema validation
            clean_dict = DeterministicJSONSanitizer.sanitize(msg.raw_llm_payload)
            validated_domain_obj = schema_cls.model_validate(clean_dict)
            
            # 3. Execute downstream business transaction
            process_fn(validated_domain_obj)

        except (json.JSONDecodeError, ValidationError) as err:
            # 4. Route to DLQ instead of crashing consumer thread
            msg = KafkaMessagePayload.model_validate_json(raw_record)
            msg.retry_count += 1
            
            print(f"🚨 Schema failure on tx {msg.transaction_id}. Routing to DLQ (Attempt {msg.retry_count}). Error: {str(err)[:80]}")
            
            self.dlq_producer.send(
                topic="payment_reconciliation_dlq",
                key=msg.transaction_id.encode("utf-8"),
                value=json.dumps({
                    "transaction_id": msg.transaction_id,
                    "error": str(err),
                    "retry_count": msg.retry_count,
                    "raw_payload": msg.raw_llm_payload
                }).encode("utf-8")
            )
