"""
Recipe 01.1: Production Bedrock Claude Client with Converse API & Decorrelated Jitter.
Author: Vatsal Shah (Lead Enterprise AI Architect)
Architecture: Claude AI Mastery Series — Volume 3
"""

import os
import sys
import time
import random
import logging
from typing import Dict, Any, List, Optional, Generator
from pydantic import BaseModel, Field, field_validator
import boto3
from botocore.config import Config
from botocore.exceptions import ClientError, BotoCoreError

# Configure structured enterprise logging
logging.basicConfig(
    level=logging.INFO,
    format='{"timestamp":"%(asctime)s","level":"%(levelname)s","logger":"%(name)s","message":"%(message)s"}'
)
logger = logging.getLogger("BedrockClaudeGateway")


class ModelMessage(BaseModel):
    role: str = Field(..., description="Role of the message sender: 'user' or 'assistant'")
    content: str = Field(..., min_length=1, description="Textual payload of the message")

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        if v not in ("user", "assistant"):
            raise ValueError(f"Invalid message role '{v}'. Must be 'user' or 'assistant'.")
        return v


class InferenceMetrics(BaseModel):
    latency_ms: float
    input_tokens: int
    output_tokens: int
    total_tokens: int
    stop_reason: str


class BedrockInferenceResponse(BaseModel):
    response_text: str
    metrics: InferenceMetrics
    region_invoked: str
    model_id: str


class EnterpriseBedrockGateway:
    """
    Industrial-grade Gateway for Anthropic Claude on AWS Bedrock.
    Implements cross-region routing, Converse API framing, and decorrelated jitter.
    """

    def __init__(
        self,
        region_name: str = "us-east-1",
        model_id: str = "us.anthropic.claude-3-5-sonnet-20241022-v2:0",
        endpoint_url: Optional[str] = None,
        max_retries: int = 5,
        base_backoff: float = 0.5,
        max_backoff: float = 32.0,
    ):
        self.region_name = region_name
        self.model_id = model_id
        self.max_retries = max_retries
        self.base_backoff = base_backoff
        self.max_backoff = max_backoff

        # Configure botocore with optimized TCP keep-alive and connection pooling
        botocore_config = Config(
            region_name=self.region_name,
            retries={"max_attempts": 0},  # Disable internal retries to enforce custom jitter logic
            connect_timeout=5,
            read_timeout=60,
            tcp_keepalive=True,
            max_pool_connections=50,
        )

        # Initialize bedrock-runtime client targeting PrivateLink interface endpoint if provided
        self.client = boto3.client(
            service_name="bedrock-runtime",
            config=botocore_config,
            endpoint_url=endpoint_url  # E.g., 'https://vpce-0a8b9f123-xyz.bedrock-runtime.us-east-1.vpce.amazonaws.com'
        )
        logger.info(f"Initialized Enterprise Bedrock Gateway targeting model {self.model_id} in {self.region_name}")

    def _calculate_decorrelated_jitter(self, current_sleep: float) -> float:
        """
        Calculates decorrelated jitter sleep duration:
        t = min(max_backoff, random.uniform(base_backoff, current_sleep * 3))
        """
        new_sleep = random.uniform(self.base_backoff, current_sleep * 3.0)
        return min(self.max_backoff, new_sleep)

    def execute_converse(
        self,
        messages: List[ModelMessage],
        system_prompt: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: int = 4096,
    ) -> BedrockInferenceResponse:
        """
        Executes synchronous reasoning via the Bedrock Converse API with full error recovery.
        """
        # Format payload according to Bedrock Converse API specifications
        formatted_messages = [
            {"role": msg.role, "content": [{"text": msg.content}]}
            for msg in messages
        ]

        system_config = [{"text": system_prompt}] if system_prompt else []
        inference_config = {
            "temperature": temperature,
            "maxTokens": max_tokens,
            "topP": 0.999,
        }

        attempt = 0
        current_sleep = self.base_backoff
        start_time = time.perf_counter()

        while True:
            attempt += 1
            try:
                logger.info(f"Dispatching inference attempt {attempt}/{self.max_retries} to {self.model_id}")
                t0 = time.perf_counter()
                
                response = self.client.converse(
                    modelId=self.model_id,
                    messages=formatted_messages,
                    system=system_config,
                    inferenceConfig=inference_config,
                )
                latency = (time.perf_counter() - t0) * 1000.0

                # Extract response contents and usage telemetry
                output_message = response["output"]["message"]
                text_content = output_message["content"][0]["text"]
                usage = response["usage"]
                stop_reason = response.get("stopReason", "end_turn")

                metrics = InferenceMetrics(
                    latency_ms=round(latency, 2),
                    input_tokens=usage["inputTokens"],
                    output_tokens=usage["outputTokens"],
                    total_tokens=usage["totalTokens"],
                    stop_reason=stop_reason,
                )

                logger.info(
                    f"Inference succeeded: {metrics.total_tokens} tokens processed in {metrics.latency_ms}ms "
                    f"[In: {metrics.input_tokens}, Out: {metrics.output_tokens}]"
                )

                return BedrockInferenceResponse(
                    response_text=text_content,
                    metrics=metrics,
                    region_invoked=self.region_name,
                    model_id=self.model_id,
                )

            except ClientError as ce:
                error_code = ce.response.get("Error", {}).get("Code", "Unknown")
                error_message = ce.response.get("Error", {}).get("Message", str(ce))

                # Identify transient vs fatal errors
                retryable_codes = [
                    "ThrottlingException",
                    "ModelStreamErrorException",
                    "ServiceUnavailableException",
                    "InternalServerException",
                    "ModelTimeoutException"
                ]

                if error_code in retryable_codes and attempt <= self.max_retries:
                    current_sleep = self._calculate_decorrelated_jitter(current_sleep)
                    logger.warning(
                        f"Transient Bedrock error '{error_code}' on attempt {attempt}. "
                        f"Backing off for {current_sleep:.2f}s. Detail: {error_message}"
                    )
                    time.sleep(current_sleep)
                    continue

                logger.error(f"Fatal Bedrock ClientError [{error_code}]: {error_message}")
                raise RuntimeError(f"Bedrock invocation failed irreversibly: {error_code} - {error_message}") from ce

            except (BotoCoreError, Exception) as ge:
                if attempt <= self.max_retries:
                    current_sleep = self._calculate_decorrelated_jitter(current_sleep)
                    logger.warning(f"Network error on attempt {attempt}: {str(ge)}. Backing off {current_sleep:.2f}s.")
                    time.sleep(current_sleep)
                    continue
                logger.error(f"Exhausted all {self.max_retries} attempts. Fatal error: {str(ge)}")
                raise ge

    def execute_converse_stream(
        self,
        messages: List[ModelMessage],
        system_prompt: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: int = 4096,
    ) -> Generator[str, None, None]:
        """
        Executes low-latency streaming inference, yielding delta text chunks as tokens arrive.
        """
        formatted_messages = [
            {"role": msg.role, "content": [{"text": msg.content}]}
            for msg in messages
        ]
        system_config = [{"text": system_prompt}] if system_prompt else []
        inference_config = {"temperature": temperature, "maxTokens": max_tokens}

        try:
            response = self.client.converse_stream(
                modelId=self.model_id,
                messages=formatted_messages,
                system=system_config,
                inferenceConfig=inference_config,
            )

            stream = response.get("stream")
            if not stream:
                raise RuntimeError("Response stream was null from Bedrock service.")

            for event in stream:
                if "contentBlockDelta" in event:
                    delta_text = event["contentBlockDelta"]["delta"]["text"]
                    yield delta_text
                elif "messageStop" in event:
                    stop_reason = event["messageStop"].get("stopReason")
                    logger.debug(f"Stream completed with stop reason: {stop_reason}")

        except ClientError as ce:
            error_code = ce.response.get("Error", {}).get("Code", "Unknown")
            logger.error(f"Streaming failed with Bedrock error: {error_code}")
            raise


# Verification Driver
if __name__ == "__main__":
    gateway = EnterpriseBedrockGateway(
        region_name="us-east-1",
        model_id="us.anthropic.claude-3-5-sonnet-20241022-v2:0"
    )

    test_prompt = [
        ModelMessage(
            role="user",
            content="Generate a 3-point architectural security checklist for AWS PrivateLink deployments."
        )
    ]

    try:
        print("\n--- Testing Synchronous Converse Execution ---")
        result = gateway.execute_converse(
            messages=test_prompt,
            system_prompt="You are a Principal Cloud Security Architect. Respond tersely and rigorously."
        )
        print(f"Model: {result.model_id} | Latency: {result.metrics.latency_ms}ms")
        print(f"Response:\n{result.response_text}")
    except Exception as e:
        print(f"Execution test halted (requires valid AWS credentials and PrivateLink routing): {e}")
