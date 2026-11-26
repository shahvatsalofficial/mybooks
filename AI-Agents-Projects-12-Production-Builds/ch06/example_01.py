from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from enum import Enum
from pydantic import BaseModel, EmailStr, Field, field_validator


class LeadSource(str, Enum):
    PRICING_FORM = "pricing_form"
    PRODUCT_SIGNUP = "product_signup"
    WEBINAR = "webinar"
    PARTNER_REFERRAL = "partner_referral"


class InboundLeadEvent(BaseModel):
    lead_id: str
    email: EmailStr
    full_name: str = Field(min_length=2, max_length=120)
    company_name: str = Field(min_length=1, max_length=160)
    role_title: str = Field(default="Unknown", max_length=120)
    source: LeadSource
    submitted_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @field_validator("email")
    @classmethod
    def lowercase_email(cls, value: str) -> str:
        return value.strip().lower()


class CanonicalLead(BaseModel):
    lead_id: str
    email: str
    canonical_domain: str
    full_name: str
    company_name: str
    role_title: str
    source: LeadSource
    dedup_fingerprint: str


MULTI_PART_TLDS = {"co.uk", "com.au", "co.in", "co.jp"}


def extract_root_domain(email: str) -> str:
    host = email.split("@", 1)[1].lower().strip()
    parts = host.split(".")
    if len(parts) >= 3 and ".".join(parts[-2:]) in MULTI_PART_TLDS:
        return ".".join(parts[-3:])
    if len(parts) >= 2:
        return ".".join(parts[-2:])
    return host


def canonicalize_lead(event: InboundLeadEvent) -> CanonicalLead:
    root_domain = extract_root_domain(str(event.email))
    fp_material = f"{event.email}:{root_domain}"
    dedup_fp = hashlib.sha256(fp_material.encode("utf-8")).hexdigest()[:16]
    return CanonicalLead(
        lead_id=event.lead_id,
        email=str(event.email),
        canonical_domain=root_domain,
        full_name=event.full_name.strip(),
        company_name=event.company_name.strip(),
        role_title=event.role_title.strip(),
        source=event.source,
        dedup_fingerprint=dedup_fp,
    )


if __name__ == "__main__":
    raw = InboundLeadEvent(
        lead_id="LD-88412",
        email="  Priya.Nair@eng.acme-cloud.co.uk ",
        full_name="Priya Nair",
        company_name="Acme Cloud Ltd",
        role_title="VP of Platform Engineering",
        source=LeadSource.PRICING_FORM,
    )
    print(canonicalize_lead(raw).model_dump_json(indent=2))
