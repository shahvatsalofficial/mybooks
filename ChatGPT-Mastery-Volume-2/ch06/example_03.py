"""
Enterprise Canary Model Gateway
Routes live production traffic across baseline and fine-tuned models with circuit breakers.
Author: Vatsal Shah, Enterprise AI Architect
"""
import random
import logging
from typing import Dict, Any
from openai import AsyncOpenAI

logger = logging.getLogger("ModelCanaryGateway")

class CanaryModelRouter:
    def __init__(
        self,
        client: AsyncOpenAI,
        baseline_model: str,
        canary_model: str,
        canary_percentage: float = 0.05
    ):
        self.client = client
        self.baseline_model = baseline_model
        self.canary_model = canary_model
        self.canary_percentage = canary_percentage
        self.canary_error_count = 0
        self.canary_total_count = 0
        self.circuit_broken = False

    async def execute_chat_completion(self, messages: list, **kwargs) -> Dict[str, Any]:
        # Determine target model
        target_model = self.baseline_model
        is_canary = False

        if not self.circuit_broken and random.random() < self.canary_percentage:
            target_model = self.canary_model
            is_canary = True

        try:
            res = await self.client.chat.completions.create(
                model=target_model,
                messages=messages,
                **kwargs
            )
            if is_canary:
                self.canary_total_count += 1
            return res

        except Exception as e:
            if is_canary:
                self.canary_error_count += 1
                self.canary_total_count += 1
                error_rate = self.canary_error_count / max(self.canary_total_count, 1)
                
                # Circuit breaker: trip if canary error rate exceeds 5%
                if self.canary_total_count >= 20 and error_rate > 0.05:
                    logger.error(f"🚨 CANARY CIRCUIT TRIPPED! Error rate: {error_rate*100:.1f}%. Rolling back to baseline.")
                    self.circuit_broken = True

            # Fallback to baseline on canary failure
            logger.warning(f"Target model {target_model} failed. Falling back to baseline {self.baseline_model}.")
            return await self.client.chat.completions.create(
                model=self.baseline_model,
                messages=messages,
                **kwargs
            )
