"""
Recipe 01.4: Universal Multi-Cloud Claude SDK Factory
Author: Vatsal Shah (Vatsal Shah)
License: Apache-2.0
"""

import os
import json
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import httpx
import boto3

class AbstractClaudeProvider(ABC):
    @abstractmethod
    def generate_message(
        self,
        messages: List[Dict[str, Any]],
        system: Optional[str] = None,
        max_tokens: int = 2048,
        temperature: float = 0.0
    ) -> Dict[str, Any]:
        pass

class AnthropicDirectProvider(AbstractClaudeProvider):
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ["ANTHROPIC_API_KEY"]
        self.url = "https://api.anthropic.com/v1/messages"

    def generate_message(self, messages, system=None, max_tokens=2048, temperature=0.0):
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        body = {
            "model": "claude-3-5-sonnet-20241022",
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        if system:
            body["system"] = system

        with httpx.Client(timeout=60.0) as client:
            resp = client.post(self.url, headers=headers, json=body)
            resp.raise_for_status()
            return resp.json()

class AWSBedrockClaudeProvider(AbstractClaudeProvider):
    def __init__(self, region_name: str = "us-east-1"):
        self.client = boto3.client("bedrock-runtime", region_name=region_name)
        self.model_id = "anthropic.claude-3-5-sonnet-20241022-v2:0"

    def generate_message(self, messages, system=None, max_tokens=2048, temperature=0.0):
        # Bedrock Converse API format
        formatted_messages = []
        for m in messages:
            role = m["role"]
            content = m["content"]
            if isinstance(content, str):
                formatted_messages.append({"role": role, "content": [{"text": content}]})
            else:
                formatted_messages.append({"role": role, "content": content})

        converse_kwargs = {
            "modelId": self.model_id,
            "messages": formatted_messages,
            "inferenceConfig": {"maxTokens": max_tokens, "temperature": temperature}
        }
        if system:
            converse_kwargs["system"] = [{"text": system}]

        response = self.client.converse(**converse_kwargs)
        
        # Normalize Bedrock output to match Anthropic Messages schema
        output_message = response["output"]["message"]
        text_content = "".join([c["text"] for c in output_message["content"] if "text" in c])
        usage = response["usage"]

        return {
            "id": response.get("ResponseMetadata", {}).get("RequestId", "bedrock-id"),
            "role": "assistant",
            "content": [{"type": "text", "text": text_content}],
            "model": self.model_id,
            "stop_reason": response.get("stopReason", "end_turn"),
            "usage": {
                "input_tokens": usage.get("inputTokens", 0),
                "output_tokens": usage.get("outputTokens", 0)
            }
        }

class ClaudeProviderFactory:
    @staticmethod
    def get_provider(provider_type: str = "anthropic", region: str = "us-east-1") -> AbstractClaudeProvider:
        if provider_type == "anthropic":
            return AnthropicDirectProvider()
        elif provider_type == "bedrock":
            return AWSBedrockClaudeProvider(region_name=region)
        raise ValueError(f"Unsupported provider: {provider_type}")
