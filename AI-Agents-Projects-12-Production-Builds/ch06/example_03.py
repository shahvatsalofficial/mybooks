from __future__ import annotations

from enum import Enum
from pydantic import BaseModel


class SuppressionReason(str, Enum):
    NONE = "none"
    DISPOSABLE_OR_FREEMAIL = "disposable_or_freemail"
    ROLE_ACCOUNT = "role_account"
    COMPETITOR_DOMAIN = "competitor_domain"
    EXISTING_ACTIVE_OPPORTUNITY = "existing_active_opportunity"


DISPOSABLE_DOMAINS = {"mailinator.com", "tempmail.org", "guerrillamail.com", "gmail.com"}
ROLE_PREFIXES = ("noreply", "no-reply", "support", "billing", "admin", "info")
COMPETITOR_DOMAINS = {"rival-ai.io", "competitor-crm.com"}
ACTIVE_CRM_OPPORTUNITY_DOMAINS = {"globex-corp.com"}


class SuppressionResult(BaseModel):
    allowed: bool
    reason: SuppressionReason


def evaluate_suppression(email: str, canonical_domain: str) -> SuppressionResult:
    local_part = email.split("@", 1)[0].lower()
    if canonical_domain in DISPOSABLE_DOMAINS:
        return SuppressionResult(allowed=False, reason=SuppressionReason.DISPOSABLE_OR_FREEMAIL)
    if any(local_part == prefix or local_part.startswith(f"{prefix}+") for prefix in ROLE_PREFIXES):
        return SuppressionResult(allowed=False, reason=SuppressionReason.ROLE_ACCOUNT)
    if canonical_domain in COMPETITOR_DOMAINS:
        return SuppressionResult(allowed=False, reason=SuppressionReason.COMPETITOR_DOMAIN)
    if canonical_domain in ACTIVE_CRM_OPPORTUNITY_DOMAINS:
        return SuppressionResult(allowed=False, reason=SuppressionReason.EXISTING_ACTIVE_OPPORTUNITY)
    return SuppressionResult(allowed=True, reason=SuppressionReason.NONE)


if __name__ == "__main__":
    samples = [
        ("priya.nair@acme-cloud.co.uk", "acme-cloud.co.uk"),
        ("test123@mailinator.com", "mailinator.com"),
        ("noreply@enterprise.io", "enterprise.io"),
        ("vp.sales@rival-ai.io", "rival-ai.io"),
    ]
    for email, dom in samples:
        res = evaluate_suppression(email, dom)
        print(f"{email:32s} -> allowed={res.allowed} reason={res.reason.value}")
