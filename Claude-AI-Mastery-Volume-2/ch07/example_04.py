"""
Recipe 07.4: Data Loss Prevention (DLP) & PII Sanitization Middleware
Author: Vatsal Shah (Opportunity4u Press)
License: Apache-2.0
"""

import re
from typing import Dict, Any, List

class EnterpriseDLPGateway:
    # High-entropy credential regex signatures
    SECRET_PATTERNS = [
        (re.compile(r"sk-ant-[a-zA-Z0-9_\-]{40,}", re.IGNORECASE), "[REDACTED_ANTHROPIC_KEY]"),
        (re.compile(r"ghp_[a-zA-Z0-9]{36,}", re.IGNORECASE), "[REDACTED_GITHUB_PAT]"),
        (re.compile(r"AKIA[0-9A-Z]{16}", re.IGNORECASE), "[REDACTED_AWS_ACCESS_KEY]"),
        (re.compile(r"xoxb-[0-9]{11,}-[0-9]{11,}-[a-zA-Z0-9]{24,}", re.IGNORECASE), "[REDACTED_SLACK_BOT_TOKEN]"),
        (re.compile(r"Bearer\s+ey[a-zA-Z0-9_\-\.]+", re.IGNORECASE), "Bearer [REDACTED_JWT_TOKEN]"),
    ]

    # Personally Identifiable Information (PII) signatures
    PII_PATTERNS = [
        (re.compile(r"\b\d{3}-\d{2}-\d{4}\b"), "[REDACTED_SSN]"),
        (re.compile(r"\b\d{4}[ -]?\d{4}[ -]?\d{4}[ -]?\d{4}\b"), "[REDACTED_CREDIT_CARD]"),
        (re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b"), "[REDACTED_EMAIL]"),
    ]

    @classmethod
    def sanitize_text(cls, text: str) -> str:
        """Applies multi-pass token masking for secrets and sensitive PII."""
        sanitized = text
        for pattern, replacement in cls.SECRET_PATTERNS:
            sanitized = pattern.sub(replacement, sanitized)
        for pattern, replacement in cls.PII_PATTERNS:
            sanitized = pattern.sub(replacement, sanitized)
        return sanitized

    @classmethod
    def sanitize_payload(cls, data: Any) -> Any:
        """Recursively sanitizes nested dictionaries, lists, and strings."""
        if isinstance(data, str):
            return cls.sanitize_text(data)
        elif isinstance(data, dict):
            return {k: cls.sanitize_payload(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [cls.sanitize_payload(v) for v in data]
        return data
