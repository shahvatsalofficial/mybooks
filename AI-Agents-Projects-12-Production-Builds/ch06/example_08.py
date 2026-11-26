from __future__ import annotations

import re
from pydantic import BaseModel

MONEY_RE = re.compile(r"\$\d+(?:\.\d+)?[MBK]?\b", re.IGNORECASE)
SERIES_RE = re.compile(r"\bSeries\s+[A-F]\b", re.IGNORECASE)
PERCENT_RE = re.compile(r"\b\d+(?:\.\d+)?%")


class GroundingCheckResult(BaseModel):
    passed: bool
    ungrounded_claims: list[str]


def verify_outreach_grounding(draft_body: str, evidence_corpus: str) -> GroundingCheckResult:
    corpus_lower = evidence_corpus.lower()
    ungrounded: list[str] = []

    for pattern in (MONEY_RE, SERIES_RE, PERCENT_RE):
        for match in pattern.findall(draft_body):
            if match.lower() not in corpus_lower:
                ungrounded.append(match)

    return GroundingCheckResult(
        passed=len(ungrounded) == 0,
        ungrounded_claims=ungrounded,
    )


if __name__ == "__main__":
    corpus = "Acme Cloud Ltd operates with 640 employees. Published SOC2 Type II attestation in Q3 2026. Stack: Kubernetes."
    hallucinated_draft = "Hi Priya, congrats on Acme Cloud's $45M Series C! Teams using Kubernetes cut MTTR by 60% with us."
    grounded_draft = "Hi Priya, noticed Acme Cloud Ltd recently published your SOC2 Type II attestation in Q3 2026 while scaling on Kubernetes."

    print("Hallucinated draft:", verify_outreach_grounding(hallucinated_draft, corpus).model_dump_json())
    print("Grounded draft:", verify_outreach_grounding(grounded_draft, corpus).model_dump_json())
