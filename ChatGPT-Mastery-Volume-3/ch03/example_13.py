# async_guardrails_orchestrator.py
import asyncio
import time
from typing import Dict, Any, List

class ParallelGuardrailsEngine:
    def __init__(self, pii_engine, jailbreak_detector, nemo_rails):
        self.pii_engine = pii_engine
        self.jailbreak_detector = jailbreak_detector
        self.nemo_rails = nemo_rails

    async def execute_pre_inference_rails(self, prompt: str, user_ctx: Dict[str, Any]) -> Dict[str, Any]:
        start_t = time.perf_counter()
        
        # Dispatch input verification tasks concurrently
        pii_task = asyncio.create_task(self.pii_engine.analyze_and_anonymize(prompt))
        jailbreak_task = asyncio.create_task(self.jailbreak_detector.score_prompt(prompt))
        topic_task = asyncio.create_task(self.nemo_rails.generate_async(messages=[{"role": "user", "content": prompt}]))
        
        # Await all parallel security checks
        pii_result, jailbreak_score, rail_result = await asyncio.gather(
            pii_task, jailbreak_task, topic_task
        )
        
        elapsed_ms = (time.perf_counter() - start_t) * 1000
        
        # Evaluate hard veto thresholds
        if jailbreak_score > 0.85:
            return {
                "blocked": True,
                "reason": "Adversarial prompt injection detected",
                "risk_score": jailbreak_score,
                "latency_ms": elapsed_ms
            }
            
        if rail_result.get("action") == "refusal":
            return {
                "blocked": True,
                "reason": rail_result.get("response"),
                "risk_score": 0.0,
                "latency_ms": elapsed_ms
            }
            
        return {
            "blocked": False,
            "sanitized_prompt": pii_result["anonymized_text"],
            "entity_map": pii_result["entity_map"],
            "latency_ms": elapsed_ms
        }
