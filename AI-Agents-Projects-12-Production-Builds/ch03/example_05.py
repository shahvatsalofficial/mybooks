from __future__ import annotations

import asyncio
from enum import Enum
from typing import List
from pydantic import BaseModel, Field


class SupportDomain(str, Enum):
    BILLING = "billing"
    TECH_OPS = "tech_ops"
    SECURITY = "security"
    ACCOUNT = "account"


class TriageDecision(BaseModel):
    primary_domain: SupportDomain
    secondary_domains: List[SupportDomain] = Field(default_factory=list)
    sentiment_score: float = Field(ge=-1.0, le=1.0)
    requests_refund_or_credit: bool
    requested_amount_usd: float = Field(default=0.0, ge=0.0)
    confidence: float = Field(ge=0.0, le=1.0)


class IntentAndSentimentClassifier:
    """Fast structured triage classifier for incoming canonical tickets."""

    async def classify(self, subject: str, body_clean: str) -> TriageDecision:
        await asyncio.sleep(0.015)  # Simulates fast classifier model call
        text = f"{subject} {body_clean}".lower()

        if any(w in text for w in ("breach", "2fa", "api key leaked", "unauthorized")):
            return TriageDecision(
                primary_domain=SupportDomain.SECURITY,
                sentiment_score=-0.85,
                requests_refund_or_credit=False,
                confidence=0.96,
            )
        if any(w in text for w in ("refund", "invoice", "credit", "charge", "sla credit")):
            amount = 500.0 if "500" in text else (45000.0 if "45,000" in text or "45000" in text else 150.0)
            return TriageDecision(
                primary_domain=SupportDomain.BILLING,
                secondary_domains=[SupportDomain.TECH_OPS] if "502" in text else [],
                sentiment_score=-0.65,
                requests_refund_or_credit=True,
                requested_amount_usd=amount,
                confidence=0.93,
            )
        if any(w in text for w in ("502", "503", "latency", "timeout", "webhook", "sdk")):
            return TriageDecision(
                primary_domain=SupportDomain.TECH_OPS,
                sentiment_score=-0.72,
                requests_refund_or_credit=False,
                confidence=0.94,
            )
        return TriageDecision(
            primary_domain=SupportDomain.ACCOUNT,
            sentiment_score=0.10,
            requests_refund_or_credit=False,
            confidence=0.88,
        )


async def main() -> None:
    clf = IntentAndSentimentClassifier()
    decision = await clf.classify(
        "502 Outage + SLA Credit",
        "Production payouts are failing with 502s; we expect a $500 SLA credit applied.",
    )
    print(decision.model_dump_json(indent=2))


if __name__ == "__main__":
    asyncio.run(main())
