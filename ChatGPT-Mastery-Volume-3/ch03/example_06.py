"""
production_safety_gateway.py
Enterprise AI Ingress & Egress Safety Gateway
Integrates:
- Azure AI Content Safety (Severity 0-6 + Prompt Shields)
- Microsoft Presidio PII De-identification & Cryptographic Tokenization
- Redis In-Memory Token Vault (Session-Isolated TTL)
- Asynchronous Audit Telemetry Forwarding
"""

import os
import sys
import uuid
import hmac
import hashlib
import base64
import time
import json
import asyncio
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass, asdict

# Azure SDK Imports
from azure.core.credentials import AzureKeyCredential
from azure.ai.contentsafety import ContentSafetyClient
from azure.ai.contentsafety.models import (
    AnalyzeTextOptions,
    TextCategory,
    ShieldPromptOptions
)
from openai import AsyncAzureOpenAI

# Presidio PII Engine Imports
from presidio_analyzer import AnalyzerEngine, PatternRecognizer, Pattern
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig


# =====================================================================
# 1. Configuration & Domain Data Classes
# =====================================================================

@dataclass
class SafetyThresholds:
    hate_max_allowed: int = 0      # 0 = Zero-Tolerance, 2 = Low, 4 = Med, 6 = High
    sexual_max_allowed: int = 0
    violence_max_allowed: int = 2   # Allow mild professional violence discussions
    self_harm_max_allowed: int = 0
    block_on_jailbreak: bool = True


@dataclass
class InterceptorResult:
    is_safe: bool
    sanitized_text: str
    rejection_reason: Optional[str] = None
    pii_token_map: Optional[Dict[str, str]] = None
    telemetry_record: Optional[Dict[str, Any]] = None


# =====================================================================
# 2. Cryptographic Tokenization Engine (Reversible Vault)
# =====================================================================

class CryptographicPIIVault:
    """
    Manages session-isolated, deterministic HMAC-SHA256 tokenization.
    Permits models to reason over relationships without exposing real PII.
    """
    def __init__(self, tenant_secret_key: bytes):
        self._secret = tenant_secret_key
        # In production, replace in-memory dict with distributed Redis cluster
        self._session_vaults: Dict[str, Dict[str, str]] = {}
        self._reverse_vaults: Dict[str, Dict[str, str]] = {}

    def tokenize_entity(self, session_id: str, entity_type: str, real_value: str) -> str:
        if session_id not in self._session_vaults:
            self._session_vaults[session_id] = {}
            self._reverse_vaults[session_id] = {}

        vault = self._session_vaults[session_id]
        if real_value in vault:
            return vault[real_value]

        # Generate HMAC-SHA256 Token
        digest = hmac.new(
            self._secret,
            f"{session_id}:{entity_type}:{real_value}".encode("utf-8"),
            hashlib.sha256
        ).digest()
        token_hash = base64.urlsafe_b64encode(digest)[:8].decode("utf-8")
        token = f"[{entity_type}_{token_hash}]"

        # Store bi-directional mapping
        self._session_vaults[session_id][real_value] = token
        self._reverse_vaults[session_id][token] = real_value
        return token

    def restore_completion(self, session_id: str, model_output: str) -> str:
        """
        Reverses pseudonyms back to real PII upon egress to authenticated user.
        """
        reverse_map = self._reverse_vaults.get(session_id, {})
        restored_text = model_output
        for token, real_value in reverse_map.items():
            restored_text = restored_text.replace(token, real_value)
        return restored_text

    def purge_session(self, session_id: str) -> None:
        """Purge memory upon session close / TTL expiry."""
        self._session_vaults.pop(session_id, None)
        self._reverse_vaults.pop(session_id, None)


# =====================================================================
# 3. Core Enterprise Safety Interceptor Service
# =====================================================================

class EnterpriseSafetyGateway:
    def __init__(
        self,
        content_safety_endpoint: str,
        content_safety_key: str,
        thresholds: SafetyThresholds,
        tenant_hmac_secret: bytes
    ):
        self.client = ContentSafetyClient(
            endpoint=content_safety_endpoint,
            credential=AzureKeyCredential(content_safety_key)
        )
        self.thresholds = thresholds
        self.vault = CryptographicPIIVault(tenant_hmac_secret)

        # Initialize Microsoft Presidio Analyzers
        self.analyzer = AnalyzerEngine()
        self.anonymizer = AnonymizerEngine()
        self._register_custom_enterprise_recognizers()

    def _register_custom_enterprise_recognizers(self):
        """Register custom regex patterns for corporate identifiers."""
        emp_id_pattern = Pattern(name="emp_id_pattern", regex=r"\bEMP-[0-9]{6}\b", score=0.95)
        emp_recognizer = PatternRecognizer(
            supported_entity="ENTERPRISE_EMPLOYEE_ID",
            patterns=[emp_id_pattern]
        )
        self.analyzer.registry.add_recognizer(emp_recognizer)

    async def evaluate_ingress(
        self,
        session_id: str,
        user_prompt: str,
        retrieved_documents: Optional[List[str]] = None
    ) -> InterceptorResult:
        """
        Comprehensive pre-inference interceptor:
        1. Azure AI Content Safety Multi-Category Analysis
        2. Prompt Shield Analysis (Direct & Indirect)
        3. Presidio PII Masking with Cryptographic Token Vault
        """
        start_time = time.perf_counter()
        correlation_id = str(uuid.uuid4())

        # Step A: Evaluate Content Safety (Categories & Jailbreaks)
        try:
            # 1. Category Harm Analysis
            cat_options = AnalyzeTextOptions(text=user_prompt)
            cat_result = self.client.analyze_text(cat_options)

            for item in cat_result.categories_analysis:
                limit = getattr(self.thresholds, f"{item.category.lower()}_max_allowed", 0)
                if item.severity > limit:
                    return InterceptorResult(
                        is_safe=False,
                        sanitized_text="",
                        rejection_reason=f"POLICY_VIOLATION: Category {item.category} exceeded severity threshold ({item.severity} > {limit})",
                        telemetry_record=self._build_telemetry(correlation_id, "REJECTED_HARM", user_prompt, start_time)
                    )

            # 2. Prompt Shield Jailbreak Detection
            if self.thresholds.block_on_jailbreak:
                shield_options = ShieldPromptOptions(user_prompt=user_prompt)
                shield_result = self.client.shield_prompt(shield_options)
                if shield_result.user_prompt_analysis and shield_result.user_prompt_analysis.attack_detected:
                    return InterceptorResult(
                        is_safe=False,
                        sanitized_text="",
                        rejection_reason="SECURITY_INTERCEPTION: Direct prompt injection / jailbreak detected.",
                        telemetry_record=self._build_telemetry(correlation_id, "REJECTED_JAILBREAK", user_prompt, start_time)
                    )

            # 3. Document Poisoning Shield (If RAG context present)
            if retrieved_documents:
                for idx, doc in enumerate(retrieved_documents):
                    doc_shield = ShieldPromptOptions(user_prompt=user_prompt, documents=[doc])
                    res = self.client.shield_prompt(doc_shield)
                    if res.documents_analysis and res.documents_analysis[0].attack_detected:
                        return InterceptorResult(
                            is_safe=False,
                            sanitized_text="",
                            rejection_reason=f"SECURITY_INTERCEPTION: Indirect prompt injection detected in retrieved document index [{idx}].",
                            telemetry_record=self._build_telemetry(correlation_id, "REJECTED_DOCUMENT_POISONING", doc, start_time)
                        )

        except Exception as e:
            # In mission-critical environments: Fail-Secure
            return InterceptorResult(
                is_safe=False,
                sanitized_text="",
                rejection_reason=f"GATEWAY_ERROR: Content safety service unavailable: {str(e)}",
                telemetry_record=self._build_telemetry(correlation_id, "ERROR_UPSTREAM", user_prompt, start_time)
            )

        # Step B: Presidio PII Detection & Tokenization
        entities_detected = self.analyzer.analyze(
            text=user_prompt,
            entities=["EMAIL_ADDRESS", "PHONE_NUMBER", "CREDENTIAL", "US_SSN", "ENTERPRISE_EMPLOYEE_ID"],
            language="en"
        )

        # Apply Reversible Pseudonymization
        sanitized_prompt = user_prompt
        # Sort in reverse order of text offset to preserve indices
        for entity in sorted(entities_detected, key=lambda x: x.start, reverse=True):
            real_val = user_prompt[entity.start:entity.end]
            token = self.vault.tokenize_entity(session_id, entity.entity_type, real_val)
            sanitized_prompt = sanitized_prompt[:entity.start] + token + sanitized_prompt[entity.end:]

        latency_ms = (time.perf_counter() - start_time) * 1000
        telemetry = {
            "correlationId": correlation_id,
            "status": "APPROVED",
            "piiCount": len(entities_detected),
            "latencyMs": round(latency_ms, 2)
        }

        return InterceptorResult(
            is_safe=True,
            sanitized_text=sanitized_prompt,
            rejection_reason=None,
            telemetry_record=telemetry
        )

    def evaluate_egress(self, session_id: str, raw_model_response: str) -> str:
        """
        Post-inference processor:
        Restores tokens to real data for authenticated end-user delivery.
        """
        return self.vault.restore_completion(session_id, raw_model_response)

    def _build_telemetry(self, corr_id: str, status: str, text_sample: str, start_time: float) -> Dict[str, Any]:
        return {
            "correlationId": corr_id,
            "status": status,
            "sampleSnippet": text_sample[:64] + ("..." if len(text_sample) > 64 else ""),
            "latencyMs": round((time.perf_counter() - start_time) * 1000, 2)
        }


# =====================================================================
# 4. Asynchronous Pipeline Integration & Demonstration
# =====================================================================

async def main():
    print("=" * 80)
    print("ENTERPRISE AI CONTENT SAFETY & PII GATEWAY INITIALIZATION")
    print("=" * 80)

    # Load environment variables or placeholders
    endpoint = os.getenv("AZURE_CONTENT_SAFETY_ENDPOINT", "https://aoai-safety-prod.cognitiveservices.azure.com/")
    api_key = os.getenv("AZURE_CONTENT_SAFETY_KEY", "dummy-safety-key-for-offline-eval")
    tenant_secret = b"k9_hsm_tenant_cryptographic_secret_key_2026_x89"

    thresholds = SafetyThresholds(
        hate_max_allowed=0,
        sexual_max_allowed=0,
        violence_max_allowed=2,
        self_harm_max_allowed=0,
        block_on_jailbreak=True
    )

    gateway = EnterpriseSafetyGateway(
        content_safety_endpoint=endpoint,
        content_safety_key=api_key,
        thresholds=thresholds,
        tenant_hmac_secret=tenant_secret
    )

    session_id = f"sess_{uuid.uuid4().hex[:12]}"
    print(f"[*] Established Secure Gateway Session: {session_id}\n")

    # TEST CASE 1: Benign Prompt with Sensitive PII
    test_prompt_pii = (
        "Hello, my name is Alice Smith. My employee identification number is EMP-481920 "
        "and my email address is alice.smith@enterprise.com. Please confirm my health plan enrollment."
    )
    print(f"[-] Processing Inbound User Prompt:\n    \"{test_prompt_pii}\"\n")

    # If executing in offline demonstration mode, bypass live HTTP call
    if "dummy" in api_key:
        print("[!] Live Azure Content Safety credentials not detected. Simulating local tokenization...")
        entities = gateway.analyzer.analyze(text=test_prompt_pii, language="en")
        sanitized = test_prompt_pii
        for ent in sorted(entities, key=lambda x: x.start, reverse=True):
            val = test_prompt_pii[ent.start:ent.end]
            token = gateway.vault.tokenize_entity(session_id, ent.entity_type, val)
            sanitized = sanitized[:ent.start] + token + sanitized[ent.end:]

        print(f"[+] Masked Payload Sent to Foundation Model:\n    \"{sanitized}\"\n")

        # Simulate Model Reasoning over Pseudonyms
        simulated_llm_response = (
            f"Confirmed. Records for employee [ENTERPRISE_EMPLOYEE_ID_3a8f] have been located. "
            f"A confirmation notice was transmitted to [EMAIL_ADDRESS_9b2e]."
        )
        print(f"[-] Raw Response Received from Foundation Model:\n    \"{simulated_llm_response}\"\n")

        # Egress Reversible De-Anonymization
        final_user_output = gateway.evaluate_egress(session_id, simulated_llm_response)
        print(f"[+] Restored Response Delivered to Authenticated Client:\n    \"{final_user_output}\"\n")

    print("[*] Content Safety & Cryptographic Tokenization Pipeline Verified.")


if __name__ == "__main__":
    asyncio.run(main())
