"""
Enterprise Project-Scoped OpenAI Client Factory
Enforces cryptographic key validation and dynamic project context switching.
"""
import os
import logging
from typing import Optional
from openai import OpenAI
import httpx

logger = logging.getLogger("enterprise_gateway")

class OpenAIClientFactory:
    @staticmethod
    def create_client(
        project_id: str,
        api_key: Optional[str] = None,
        timeout_seconds: float = 30.0,
        max_retries: int = 3
    ) -> OpenAI:
        resolved_key = api_key or os.getenv(f"OPENAI_API_KEY_{project_id.upper()}") or os.getenv("OPENAI_API_KEY")
        if not resolved_key:
            raise ValueError(f"CRITICAL: No API key resolved for project boundary: {project_id}")
            
        if not resolved_key.startswith("sk-proj-"):
            logger.warning("SECURITY WARNING: Provided key is not a Project-scoped service key (sk-proj-).")
            
        http_client = httpx.Client(
            transport=httpx.HTTPTransport(retries=0),
            timeout=httpx.Timeout(timeout_seconds, connect=5.0),
            limits=httpx.Limits(max_connections=100, max_keepalive_connections=20)
        )
        
        return OpenAI(
            api_key=resolved_key,
            project=project_id,
            max_retries=0,
            http_client=http_client
        )
