"""
AWS Bedrock Sovereign Enterprise Claude Gateway
Author: Vatsal Shah, Lead Enterprise AI Architect
Publisher: Opportunity4u Press (c) 2026
"""

import os
import json
import boto3
from botocore.config import Config
from typing import Dict, Any, Generator

class BedrockClaudeGateway:
    """
    Sovereign enterprise client invoking Claude on AWS Bedrock
    with IAM SigV4 authentication and VPC endpoint support.
    """
    def __init__(self, region_name: str = "us-east-1"):
        # Configure robust connection pooling and retry behavior
        boto_config = Config(
            region_name=region_name,
            retries={"max_attempts": 5, "mode": "adaptive"},
            connect_timeout=10,
            read_timeout=120
        )
        self.bedrock = boto3.client(
            service_name="bedrock-runtime",
            config=boto_config
        )
        self.sonnet_model_id = "anthropic.claude-3-5-sonnet-20241022-v2:0"
        self.haiku_model_id = "anthropic.claude-3-5-haiku-20241022-v1:0"

    def invoke_streaming_claude(
        self,
        prompt: str,
        system_prompt: str = "",
        max_tokens: int = 4096,
        temperature: float = 0.0,
        use_haiku: bool = False
    ) -> Generator[str, None, None]:
        """
        Invokes Claude on AWS Bedrock and yields streaming text chunks.
        """
        model_id = self.haiku_model_id if use_haiku else self.sonnet_model_id

        # Format native Anthropic Messages API payload
        native_request = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [{"role": "user", "content": prompt}]
        }
        if system_prompt:
            native_request["system"] = system_prompt

        response = self.bedrock.invoke_model_with_response_stream(
            modelId=model_id,
            body=json.dumps(native_request)
        )

        stream = response.get("body")
        if stream:
            for event in stream:
                chunk = event.get("chunk")
                if chunk:
                    chunk_json = json.loads(chunk.get("bytes").decode())
                    chunk_type = chunk_json.get("type")
                    if chunk_type == "content_block_delta":
                        delta = chunk_json.get("delta", {})
                        if delta.get("type") == "text_delta":
                            yield delta.get("text", "")

# Verification script
if __name__ == "__main__":
    gateway = BedrockClaudeGateway()
    print("Testing Sovereign AWS Bedrock Stream...")
    for text_token in gateway.invoke_streaming_claude(
        prompt="Explain the difference between GQA and MQA in transformer self-attention in two concise bullet points.",
        system_prompt="You are a principal hardware AI architect. Answer concisely."
    ):
        print(text_token, end="", flush=True)
    print("\n[Stream Complete]")
