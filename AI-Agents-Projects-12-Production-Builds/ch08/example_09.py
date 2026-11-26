from __future__ import annotations

import re
from typing import List, Tuple
from pydantic import BaseModel, Field


class PiiFinding(BaseModel):
    entity_type: str
    start: int
    end: int
    masked_preview: str


class PiiScanReport(BaseModel):
    has_pii: bool
    findings: List[PiiFinding] = Field(default_factory=list)
    redacted_text: str


class BidirectionalPiiScanner:
    """Detects and redacts SSNs, Luhn-valid cards, emails, and API secrets."""

    SSN_RE = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
    EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
    API_KEY_RE = re.compile(r"\b(?:sk-[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16})\b")
    CARD_RE = re.compile(r"\b(?:\d[ -]*?){13,16}\b")

    @staticmethod
    def _luhn_valid(digits: str) -> bool:
        nums = [int(ch) for ch in digits if ch.isdigit()]
        if len(nums) < 13 or len(nums) > 16:
            return False
        checksum = 0
        reverse = nums[::-1]
        for idx, d in enumerate(reverse):
            if idx % 2 == 1:
                d *= 2
                if d > 9:
                    d -= 9
            checksum += d
        return checksum % 10 == 0

    def scan_and_redact(self, text: str) -> PiiScanReport:
        spans: List[Tuple[int, int, str]] = []
        for m in self.SSN_RE.finditer(text):
            spans.append((m.start(), m.end(), "SSN"))
        for m in self.EMAIL_RE.finditer(text):
            spans.append((m.start(), m.end(), "EMAIL"))
        for m in self.API_KEY_RE.finditer(text):
            spans.append((m.start(), m.end(), "API_SECRET"))
        for m in self.CARD_RE.finditer(text):
            digits = re.sub(r"\D", "", m.group(0))
            if self._luhn_valid(digits):
                spans.append((m.start(), m.end(), "PAYMENT_CARD"))

        spans.sort(key=lambda s: s[0])
        findings: List[PiiFinding] = []
        out_parts: List[str] = []
        cursor = 0
        for start, end, etype in spans:
            if start < cursor:
                continue
            out_parts.append(text[cursor:start])
            out_parts.append(f"[REDACTED_{etype}]")
            findings.append(
                PiiFinding(
                    entity_type=etype,
                    start=start,
                    end=end,
                    masked_preview=f"[REDACTED_{etype}]",
                )
            )
            cursor = end
        out_parts.append(text[cursor:])

        return PiiScanReport(
            has_pii=len(findings) > 0,
            findings=findings,
            redacted_text="".join(out_parts),
        )


def demo_pii_scanner() -> None:
    scanner = BidirectionalPiiScanner()
    sample = (
        "Contact alice@acme.com (SSN 123-45-6789) using key AKIAIOSFODNN7EXAMPLE "
        "or trace ID 1234567890123456."
    )
    report = scanner.scan_and_redact(sample)
    print(f"PII detected: {report.has_pii} | Count: {len(report.findings)}")
    print(f"Redacted: {report.redacted_text}")


if __name__ == "__main__":
    demo_pii_scanner()
