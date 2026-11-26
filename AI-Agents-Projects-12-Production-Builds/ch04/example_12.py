from __future__ import annotations

import re
from typing import List, Set
from pydantic import BaseModel


class AuditVerdict(BaseModel):
    passed: bool
    extracted_numbers: List[str]
    ungrounded_numbers: List[str]


class ClaimCitationVerifier:
    """Verifies that every numeric claim in memo prose traces to verified inputs."""

    NUM_RE = re.compile(r"(?<![A-Za-z])\$?-?\d+(?:,\d{3})*(?:\.\d+)?%?")

    @classmethod
    def audit(cls, memo_text: str, approved_values: Set[str]) -> AuditVerdict:
        found = cls.NUM_RE.findall(memo_text)
        normalized_approved = {v.replace("$", "").replace(",", "").replace("%", "") for v in approved_values}
        ungrounded: List[str] = []

        for token in found:
            clean = token.replace("$", "").replace(",", "").replace("%", "")
            if clean not in normalized_approved:
                ungrounded.append(token)

        return AuditVerdict(
            passed=(len(ungrounded) == 0),
            extracted_numbers=found,
            ungrounded_numbers=ungrounded,
        )


if __name__ == "__main__":
    approved = {"2025", "12.84", "13.24", "14.64", "1.25"}
    clean_memo = "In 2025, revenue reached $12.84B (+14.64% YoY) with 13.24% FCF margin and 1.25x net leverage."
    bad_memo = "In 2025, revenue reached $12.84B with 18.40% FCF margin."
    print("Clean memo audit:", ClaimCitationVerifier.audit(clean_memo, approved).model_dump())
    print("Hallucinated memo audit:", ClaimCitationVerifier.audit(bad_memo, approved).model_dump())
