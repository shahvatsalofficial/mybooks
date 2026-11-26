"""
Memory Ingestion Sanitizer: Scans incoming external documents before committing
to episodic vector storage, filtering adversarial prompt injection vectors.
"""

import re
from typing import Tuple, Optional


class MemorySecuritySanitizer:
    """Pre-screens candidate memories for adversarial prompt injections and PII."""

    SUSPICIOUS_PATTERNS = [
        r"ignore\s+(all\s+)?previous\s+instructions",
        r"system\s+override",
        r"you\s+are\s+now\s+in\s+developer\s+mode",
        r"<system_constitution>",
        r"export\s+all\s+environment\s+variables",
        r"http[s]?://[^\s]+\?exfil=",
    ]

    def __init__(self):
        self.compiled_regexes = [
            re.compile(pattern, re.IGNORECASE) for pattern in self.SUSPICIOUS_PATTERNS
        ]

    def sanitize_for_storage(self, raw_text: str) -> Tuple[bool, str, Optional[str]]:
        """
        Inspects text payload for adversarial vectors.
        Returns: (is_safe, sanitized_text, threat_reason)
        """
        for regex in self.compiled_regexes:
            if regex.search(raw_text):
                return (
                    False,
                    "",
                    f"ADVERSARIAL_INJECTION_DETECTED: Matched restricted pattern '{regex.pattern}'",
                )

        cleaned = re.sub(r"sk-[a-zA-Z0-9]{32,}", "[REDACTED_API_KEY]", raw_text)
        cleaned = re.sub(r"AKIA[0-9A-Z]{16}", "[REDACTED_AWS_KEY]", cleaned)

        cleaned = cleaned.replace("<system_constitution>", "&lt;system_constitution&gt;")
        cleaned = cleaned.replace("</system_constitution>", "&lt;/system_constitution&gt;")

        return True, cleaned, None
