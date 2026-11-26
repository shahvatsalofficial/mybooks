"""
Recipe 08.3: Multi-Provider HA Failover Client (Anthropic Direct -> AWS Bedrock -> GCP Vertex AI)
Author: Vatsal Shah (Opportunity4u Press)
License: Apache-2.0
"""

import os
import logging
from typing import Dict, Any, List, Optional
import httpx
import boto3
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("MultiProviderRouter")

class MultiProviderClaudeClient:
    def __init__(self, anthropic_key: str, aws_region: str = "us-east-1"):
        self.anthropic_key = anthropic_key
        self.aws_region = aws_region
        self.http_client = httpx.AsyncClient(timeout=30.0)
        self.bedrock_client = boto3.client("bedrock-runtime", region_name=aws_region)

    async def generate_resilient(self, messages: List[Dict[str, Any]], system_prompt: Optional[str] = None) -> str:
        """Executes query with seamless failover across Anthropic Direct and AWS Bedrock."""
        # Tier 1: Primary Anthropic Direct API
        try:
            logger.info("Routing query to Primary: Anthropic Direct Messages API")
            payload = {
                "model": "claude-3-5-sonnet-20241022",
                "max_tokens": 2048,
                "messages": messages
            }
            if system_prompt:
                payload["system"] = system_prompt

            response = await self.http_client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": self.anthropic_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json"
                },
                json=payload
            )

            if response.status_code == 200:
                data = response.json()
                return data["content"][0]["text"]

            # If upstream returns 529 (Overloaded), 503, or 500, trigger secondary failover
            if response.status_code in (500, 502, 503, 529):
                logger.warning(f"Primary Anthropic returned HTTP {response.status_code}. Initiating AWS Bedrock Failover...")
                return self._invoke_aws_bedrock(messages, system_prompt)

            response.raise_for_status()

        except (httpx.ConnectTimeout, httpx.ReadTimeout, httpx.ConnectError) as net_err:
            logger.error(f"Primary Anthropic network error: {net_err}. Failing over to AWS Bedrock...")
            return self._invoke_aws_bedrock(messages, system_prompt)

    def _invoke_aws_bedrock(self, messages: List[Dict[str, Any]], system_prompt: Optional[str]) -> str:
        """Secondary Failover Route: AWS Bedrock Claude 3.5 Sonnet."""
        logger.info(f"Executing Secondary Route via AWS Bedrock in {self.aws_region}")
        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 2048,
            "messages": messages
        }
        if system_prompt:
            body["system"] = system_prompt

        response = self.bedrock_client.invoke_model(
            modelId="anthropic.claude-3-5-sonnet-20241022-v2:0",
            body=json.dumps(body),
            contentType="application/json",
            accept="application/json"
        )
        response_body = json.loads(response["body"].read())
        return response_body["content"][0]["text"]
