"""
Recipe 03.1: Enterprise Asynchronous Claude Client for Google Cloud Vertex AI.
Author: Vatsal Shah (Lead Enterprise AI Architect)
Architecture: Claude AI Mastery Series — Volume 3
"""

import asyncio
import json
import logging
import time
from typing import AsyncGenerator, Dict, Any, List, Optional
import google.auth
from google.auth.transport.requests import Request
import httpx
from pydantic import BaseModel, Field

# Configure structured enterprise logging
logger = logging.getLogger("VertexClaudeClient")
logger.setLevel(logging.INFO)


class ModelUsage(BaseModel):
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_input_tokens: int = 0
    cache_creation_input_tokens: int = 0


class VertexClaudeStreamResponse(BaseModel):
    event_type: str
    delta_text: str = ""
    usage: Optional[ModelUsage] = None


class VertexClaudeClient:
    """
    Production client for Anthropic Claude 3.5 Sonnet on Google Cloud Vertex AI.
    Handles Workload Identity OAuth2 token management and streaming raw predictions.
    """

    def __init__(
        self,
        project_id: str,
        region: str = "us-east5",
        model_id: str = "claude-3-5-sonnet@20241022",
        timeout_seconds: float = 60.0
    ):
        self.project_id = project_id
        self.region = region
        self.model_id = model_id
        self.timeout = timeout_seconds

        # Resolve credentials using standard Google Cloud Application Default Credentials (ADC)
        # In GKE, this automatically activates Workload Identity Federation
        self.credentials, self.detected_project = google.auth.default(
            scopes=["https://www.googleapis.com/auth/cloud-platform"]
        )
        self.auth_request = Request()
        self._refresh_token_if_needed()

        self.endpoint_url = (
            f"https://{self.region}-aiplatform.googleapis.com/v1/"
            f"projects/{self.project_id}/locations/{self.region}/"
            f"publishers/anthropic/models/{self.model_id}:streamRawPredict"
        )
        logger.info(f"Initialized VertexClaudeClient for [{self.model_id}] in [{self.region}]")

    def _refresh_token_if_needed(self) -> None:
        """Refreshes the OAuth2 access token if missing or within 5 minutes of expiration."""
        now = time.time()
        if not self.credentials.valid or (self.credentials.expiry and self.credentials.expiry.timestamp() - now < 300):
            logger.info("Refreshing Google Cloud OAuth2 access token...")
            self.credentials.refresh(self.auth_request)
            logger.info(f"Token refreshed successfully. Expires at: {self.credentials.expiry}")

    async def stream_chat(
        self,
        messages: List[Dict[str, Any]],
        system_prompt: str = "",
        max_tokens: int = 4096,
        temperature: float = 0.2,
        tools: Optional[List[Dict[str, Any]]] = None
    ) -> AsyncGenerator[VertexClaudeStreamResponse, None]:
        """
        Executes a streaming inference call against Vertex AI Claude using Server-Sent Events (SSE).
        """
        self._refresh_token_if_needed()

        headers = {
            "Authorization": f"Bearer {self.credentials.token}",
            "Content-Type": "application/json; charset=utf-8",
            "Accept": "text/event-stream",
        }

        # Build Anthropic Messages API payload
        payload: Dict[str, Any] = {
            "anthropic_version": "vertex-2023-10-16",
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": True,
        }

        if system_prompt:
            payload["system"] = system_prompt
        if tools:
            payload["tools"] = tools

        limits = httpx.Limits(max_keepalive_connections=50, max_connections=200)
        async with httpx.AsyncClient(limits=limits, timeout=self.timeout) as client:
            try:
                async with client.stream("POST", self.endpoint_url, headers=headers, json=payload) as response:
                    if response.status_code != 200:
                        error_body = await response.aread()
                        logger.error(f"Vertex AI API Error [{response.status_code}]: {error_body.decode('utf-8')}")
                        raise RuntimeError(f"Vertex AI call failed with status {response.status_code}: {error_body.decode('utf-8')}")

                    buffer = ""
                    async for line in response.aiter_lines():
                        if not line or line.startswith(":"):
                            continue

                        if line.startswith("data: "):
                            data_str = line[6:].strip()
                            if data_str == "[DONE]":
                                break

                            try:
                                chunk = json.loads(data_str)
                                chunk_type = chunk.get("type", "")

                                if chunk_type == "content_block_delta":
                                    delta = chunk.get("delta", {})
                                    if delta.get("type") == "text_delta":
                                        yield VertexClaudeStreamResponse(
                                            event_type="text_delta",
                                            delta_text=delta.get("text", "")
                                        )

                                elif chunk_type == "message_delta":
                                    usage_data = chunk.get("usage", {})
                                    yield VertexClaudeStreamResponse(
                                        event_type="message_delta",
                                        usage=ModelUsage(
                                            output_tokens=usage_data.get("output_tokens", 0)
                                        )
                                    )

                                elif chunk_type == "message_start":
                                    msg = chunk.get("message", {})
                                    usage_data = msg.get("usage", {})
                                    yield VertexClaudeStreamResponse(
                                        event_type="message_start",
                                        usage=ModelUsage(
                                            input_tokens=usage_data.get("input_tokens", 0),
                                            cache_read_input_tokens=usage_data.get("cache_read_input_tokens", 0),
                                            cache_creation_input_tokens=usage_data.get("cache_creation_input_tokens", 0)
                                        )
                                    )

                            except json.JSONDecodeError:
                                logger.warning(f"Failed to decode SSE chunk: {data_str}")
                                continue

            except httpx.RequestError as exc:
                logger.error(f"Transport failure while streaming from Vertex AI: {str(exc)}")
                raise ConnectionError(f"Vertex AI connection failure: {str(exc)}") from exc
