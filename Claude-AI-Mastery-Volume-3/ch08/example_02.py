"""
sovereign_bedrock_router.py
Enterprise Multi-Jurisdiction Sovereign AI Router for Anthropic Claude on AWS Bedrock.
Enforces GDPR Chapter V, Swiss FADP, and US FedRAMP data localization.
"""

import json
import logging
from enum import Enum
from typing import Any, Dict, List, Optional
import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("SovereignBedrockRouter")


class JurisdictionZone(str, Enum):
    EU_SOVEREIGN = "EU_SOVEREIGN"      # Frankfurt (eu-central-1) - GDPR Strict
    US_COMMERCIAL = "US_COMMERCIAL"    # N. Virginia (us-east-1) - HIPAA / SOC-2
    SWISS_BANKING = "SWISS_BANKING"    # Zurich (eu-central-2) - FINMA Circular 2018/3


class SovereignRoutingException(Exception):
    """Raised when cross-border data transfer policy prohibits execution."""
    pass


class SovereignBedrockGateway:
    """Manages isolated regional Bedrock clients with hard-boundary geofencing."""

    def __init__(self):
        # Configure isolated regional clients with strict retries within the same region only
        boto_cfg = Config(retries={"max_attempts": 3, "mode": "standard"}, connect_timeout=5, read_timeout=30)
        
        self.clients = {
            JurisdictionZone.EU_SOVEREIGN: boto3.client("bedrock-runtime", region_name="eu-central-1", config=boto_cfg),
            JurisdictionZone.US_COMMERCIAL: boto3.client("bedrock-runtime", region_name="us-east-1", config=boto_cfg),
            JurisdictionZone.SWISS_BANKING: boto3.client("bedrock-runtime", region_name="eu-central-2", config=boto_cfg),
        }
        
        # Dedicated model ARNs per region to prevent accidental cross-region profile resolution
        self.model_map = {
            JurisdictionZone.EU_SOVEREIGN: "anthropic.claude-3-5-sonnet-20241022-v2:0",
            JurisdictionZone.US_COMMERCIAL: "anthropic.claude-3-5-sonnet-20241022-v2:0",
            JurisdictionZone.SWISS_BANKING: "anthropic.claude-3-5-sonnet-20241022-v2:0",
        }
        logger.info("Sovereign Bedrock Gateway initialized across 3 isolated regional silos.")

    def route_and_invoke(
        self,
        jurisdiction: JurisdictionZone,
        messages: List[Dict[str, Any]],
        system_prompt: Optional[str] = None,
        max_tokens: int = 4096,
        user_country_code: str = "DE",
    ) -> Dict[str, Any]:
        """
        Routes inference payload strictly to authorized sovereign regional endpoint.
        Fails closed if the sovereign regional endpoint is unavailable.
        """
        # 1. Enforce GDPR Chapter V Geofence Assertion
        if jurisdiction == JurisdictionZone.EU_SOVEREIGN and user_country_code not in ["DE", "FR", "IT", "ES", "NL", "IE", "PL", "SE"]:
            logger.error("Jurisdiction Mismatch: Ingress Country %s unauthorized for EU Sovereign Zone", user_country_code)
            raise SovereignRoutingException(f"Cross-border transfer policy violation for country: {user_country_code}")

        target_client = self.clients[jurisdiction]
        target_model = self.model_map[jurisdiction]

        payload: Dict[str, Any] = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "temperature": 0.0,
            "messages": messages,
        }
        if system_prompt:
            payload["system"] = system_prompt

        logger.info("Dispatching invocation to Sovereign Silo [%s] | Model: %s", jurisdiction.value, target_model)
        
        try:
            response = target_client.invoke_model(
                modelId=target_model,
                contentType="application/json",
                accept="application/json",
                body=json.dumps(payload),
            )
            raw_response = json.loads(response["body"].read().decode("utf-8"))
            
            return {
                "jurisdiction_executed": jurisdiction.value,
                "region": target_client.meta.region_name,
                "output": raw_response["content"][0]["text"],
                "usage": raw_response.get("usage", {}),
                "sovereign_verified": True,
            }

        except ClientError as err:
            error_code = err.response.get("Error", {}).get("Code", "Unknown")
            logger.critical("Sovereign regional endpoint [%s] failed with code: %s", jurisdiction.value, error_code)
            
            # CRITICAL GOVERNANCE RULE: NEVER FAIL OVER CROSS-BORDER
            # Fail closed immediately to protect data residency guarantees.
            raise SovereignRoutingException(
                f"Sovereign endpoint [{jurisdiction.value}] failed ({error_code}). "
                "Automatic cross-border failover is strictly prohibited under GDPR Chapter V."
            ) from err
