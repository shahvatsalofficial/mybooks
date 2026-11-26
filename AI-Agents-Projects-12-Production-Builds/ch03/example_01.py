from __future__ import annotations

import hashlib
import re
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


class ChannelType(str, Enum):
    ZENDESK = "zendesk"
    INTERCOM = "intercom"
    EMAIL = "email"
    SLACK = "slack"


class CustomerTier(str, Enum):
    ENTERPRISE = "enterprise"
    GROWTH = "growth"
    STARTER = "starter"


class AttachmentRef(BaseModel):
    filename: str
    mime_type: str
    size_bytes: int = Field(ge=0)
    sha256: str
    storage_uri: str


class TenantEntitlement(BaseModel):
    tenant_id: str
    company_name: str
    tier: CustomerTier
    mrr_usd: float = Field(ge=0.0)
    p1_sla_minutes: int = Field(gt=0)
    p2_sla_minutes: int = Field(gt=0)
    max_auto_refund_usd: float = Field(ge=0.0)


class CanonicalTicket(BaseModel):
    ticket_id: str
    external_thread_id: str
    idempotency_key: str
    channel: ChannelType
    sender_email: str
    subject: str
    body_clean: str
    raw_char_count: int = Field(ge=0)
    received_at: datetime
    attachments: List[AttachmentRef] = Field(default_factory=list)
    entitlement: TenantEntitlement
    correlation_tags: List[str] = Field(default_factory=list)

    @field_validator("body_clean")
    @classmethod
    def ensure_non_empty_body(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("Normalized ticket body cannot be empty.")
        return stripped


class QuoteStripper:
    """Removes email reply chains, HTML tags, and boilerplate signatures."""

    HTML_TAG_RE = re.compile(r"<[^>]+>")
    EMAIL_QUOTE_RE = re.compile(
        r"(?im)^(On .+ wrote:|From:\s.+|-----Original Message-----).*$",
        re.DOTALL,
    )
    SIG_RE = re.compile(r"(?m)^--\s*\n.*$", re.DOTALL)

    @classmethod
    def clean(cls, raw_text: str) -> str:
        no_html = cls.HTML_TAG_RE.sub(" ", raw_text)
        no_quotes = cls.EMAIL_QUOTE_RE.sub("", no_html)
        no_sig = cls.SIG_RE.sub("", no_quotes)
        collapsed = re.sub(r"\s+", " ", no_sig).strip()
        return collapsed


class ChannelAdapter:
    """Normalizes heterogeneous support webhooks into CanonicalTicket objects."""

    def __init__(self, entitlement_lookup: Dict[str, TenantEntitlement]) -> None:
        self._entitlements = entitlement_lookup

    def _resolve_entitlement(self, email: str) -> TenantEntitlement:
        domain = email.split("@")[-1].lower()
        if domain in self._entitlements:
            return self._entitlements[domain]
        return TenantEntitlement(
            tenant_id=f"ten_{hashlib.sha256(domain.encode()).hexdigest()[:8]}",
            company_name=domain,
            tier=CustomerTier.STARTER,
            mrr_usd=99.0,
            p1_sla_minutes=240,
            p2_sla_minutes=720,
            max_auto_refund_usd=25.0,
        )

    def normalize(self, channel: ChannelType, payload: Dict[str, Any]) -> CanonicalTicket:
        if channel == ChannelType.ZENDESK:
            sender = payload["requester"]["email"].lower()
            raw_body = payload["comment"]["html_body"]
            thread_id = f"zd_{payload['ticket_id']}"
            event_id = str(payload["audit_id"])
            subject = payload.get("subject", "Support Inquiry")
        elif channel == ChannelType.SLACK:
            sender = payload["user_profile"]["email"].lower()
            raw_body = payload["event"]["text"]
            thread_id = f"sl_{payload['event']['channel']}_{payload['event']['thread_ts']}"
            event_id = payload["event_id"]
            subject = f"Slack Thread {payload['event']['channel']}"
        elif channel == ChannelType.INTERCOM:
            sender = payload["user"]["email"].lower()
            raw_body = payload["conversation_parts"][0]["body"]
            thread_id = f"ic_{payload['conversation_id']}"
            event_id = payload["delivery_id"]
            subject = payload.get("title", "Intercom Live Chat")
        else:
            sender = payload["from_email"].lower()
            raw_body = payload["text_body"]
            thread_id = f"em_{payload['message_id']}"
            event_id = payload["message_id"]
            subject = payload.get("subject", "Email Support")

        clean_body = QuoteStripper.clean(raw_body)
        idem = hashlib.sha256(f"{channel.value}:{event_id}".encode()).hexdigest()[:24]
        return CanonicalTicket(
            ticket_id=f"TKT-{idem[:10].upper()}",
            external_thread_id=thread_id,
            idempotency_key=idem,
            channel=channel,
            sender_email=sender,
            subject=subject,
            body_clean=clean_body,
            raw_char_count=len(raw_body),
            received_at=datetime.now(timezone.utc),
            entitlement=self._resolve_entitlement(sender),
        )


if __name__ == "__main__":
    entitlements = {
        "acme-fintech.io": TenantEntitlement(
            tenant_id="ten_acme_01",
            company_name="Acme Fintech Corp",
            tier=CustomerTier.ENTERPRISE,
            mrr_usd=18500.0,
            p1_sla_minutes=15,
            p2_sla_minutes=60,
            max_auto_refund_usd=500.0,
        )
    }
    adapter = ChannelAdapter(entitlements)
    zd_payload = {
        "ticket_id": 88412,
        "audit_id": "aud_99120",
        "subject": "502 Bad Gateway on /v2/payouts",
        "requester": {"email": "cto@acme-fintech.io"},
        "comment": {
            "html_body": "<p>Production payouts are failing with 502s since 06:40 UTC.</p>"
            "On Mon, Nov 25, 2026 at 06:10 AM Support wrote: > Please share logs."
        },
    }
    ticket = adapter.normalize(ChannelType.ZENDESK, zd_payload)
    print(ticket.model_dump_json(indent=2))
