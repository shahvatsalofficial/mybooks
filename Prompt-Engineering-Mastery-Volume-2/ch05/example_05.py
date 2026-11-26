import hashlib
import json
from typing import Dict, Any, Callable, Optional

class RedisPipelineCheckpointer:
    def __init__(self, redis_client: Any, ttl_seconds: int = 86400):
        self.redis = redis_client
        self.ttl = ttl_seconds

    def generate_trace_id(self, tenant_id: str, raw_payload: str) -> str:
        hasher = hashlib.sha256()
        hasher.update(tenant_id.encode("utf-8"))
        hasher.update(raw_payload.encode("utf-8"))
        return f"trace_{hasher.hexdigest()[:16]}"

    def execute_idempotent_step(
        self,
        trace_id: str,
        step_name: str,
        step_fn: Callable[[], Dict[str, Any]]
    ) -> Dict[str, Any]:
        cache_key = f"pipeline:{trace_id}:{step_name}"
        
        # 1. Check existing checkpoint
        cached = self.redis.get(cache_key)
        if cached:
            print(f"⚡ Checkpoint hit for {step_name}. Returning cached state.")
            return json.loads(cached)

        # 2. Execute underlying stage
        result = step_fn()

        # 3. Persist checkpoint atomically
        self.redis.setex(cache_key, self.ttl, json.dumps(result))
        return result

# Example Resilient Pipeline Runner
class ResilientChainedService:
    def __init__(self, checkpointer: RedisPipelineCheckpointer, pipeline: ChainedEnterprisePipeline):
        self.checkpointer = checkpointer
        self.pipeline = pipeline

    def run(self, tenant_id: str, raw_ticket: str) -> Dict[str, Any]:
        trace_id = self.checkpointer.generate_trace_id(tenant_id, raw_ticket)

        # Stage 1: Cached Extraction
        entities_data = self.checkpointer.execute_idempotent_step(
            trace_id, "stage_1_extract",
            lambda: self.pipeline.stage_1_extract(raw_ticket).model_dump()
        )
        entities = ExtractedEntities(**entities_data)

        # Stage 2: Cached Policy Underwriting
        policy_data = self.checkpointer.execute_idempotent_step(
            trace_id, "stage_2_policy",
            lambda: self.pipeline.stage_2_evaluate_policy(entities).model_dump()
        )
        policy = PolicyEvaluation(**policy_data)

        # Stage 3: Cached Resolution Dispatch
        resolution_data = self.checkpointer.execute_idempotent_step(
            trace_id, "stage_3_resolution",
            lambda: self.pipeline.stage_3_synthesize_response(entities, policy).model_dump()
        )
        
        return {
            "trace_id": trace_id,
            "entities": entities_data,
            "policy": policy_data,
            "resolution": resolution_data
        }
