from __future__ import annotations

import re
from typing import List, Set
from pydantic import BaseModel, Field


class CitationAuditResult(BaseModel):
    is_grounded: bool
    cited_doc_ids: List[str] = Field(default_factory=list)
    unauthorized_or_hallucinated: List[str] = Field(default_factory=list)


class CitationGroundingVerifier:
    """Validates that every response citation maps to an authorized retrieved doc."""

    def verify(self, response_text: str, authorized_doc_ids: Set[str]) -> CitationAuditResult:
        cited = re.findall(r"\[([a-zA-Z0-9_\-]+)\]", response_text)
        unique_cited = list(dict.fromkeys(cited))
        invalid = [doc for doc in unique_cited if doc not in authorized_doc_ids]
        return CitationAuditResult(
            is_grounded=(len(unique_cited) > 0 and len(invalid) == 0),
            cited_doc_ids=unique_cited,
            unauthorized_or_hallucinated=invalid,
        )


def demo_citation_verifier() -> None:
    verifier = CitationGroundingVerifier()
    ans = "Rotate KMS keys every 90 days [doc_eng_runbook]. Bonus tiers are in [doc_hr_bonus]."
    res = verifier.verify(ans, authorized_doc_ids={"doc_eng_runbook"})
    print(f"Grounded: {res.is_grounded} | Invalid citations: {res.unauthorized_or_hallucinated}")


if __name__ == "__main__":
    demo_citation_verifier()
