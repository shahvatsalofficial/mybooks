"""
Architectural Drill 6: Unicode Homoglyph & Delimiter Sanitization Pipeline
"""

import unicodedata
import re
from pydantic import BaseModel, Field, field_validator

FORBIDDEN_DELIMITERS = [
    "<|im_start|>", "<|im_end|>", "system:", "assistant:", "[INST]", "[/INST]", "```"
]

class HardenedTicketPayload(BaseModel):
    customer_id: str = Field(..., regex=r"^[A-Z0-9\-]{8,24}$")
    subject: str = Field(..., min_length=5, max_length=120)
    body: str = Field(..., min_length=10, max_length=2000)

    @field_validator("subject", "body")
    @classmethod
    def sanitize_and_normalize(cls, value: str) -> str:
        # 1. Normalize Unicode to NFKC (Compatibility Decomposition + Canonical Composition)
        normalized = unicodedata.normalize("NFKC", value)
        
        # 2. Check for Prompt Injection Delimiters
        for delimiter in FORBIDDEN_DELIMITERS:
            if delimiter in normalized.lower():
                raise ValueError(f"Security Policy Violation: Forbidden control delimiter detected.")

        # 3. Strip non-printable or invisible control characters (zero-width spaces, soft hyphens)
        cleaned = "".join(ch for ch in normalized if unicodedata.category(ch) != "Cf" and ord(ch) >= 32)

        # 4. Enforce strict character sets for subjects
        if not re.match(r"^[\w\s\.,\?!'\-–—:;\"#@\(\)]+$", cleaned):
            raise ValueError("Input text contains illegal characters or script mixing.")

        return cleaned.strip()

# Verification
valid_ticket = HardenedTicketPayload(
    customer_id="CUST-8839-A",
    subject="Login latency degradation on EU-West",
    body="Our engineers noticed increased response times exceeding 4000ms after the recent deployment."
)
assert valid_ticket.subject == "Login latency degradation on EU-West"
