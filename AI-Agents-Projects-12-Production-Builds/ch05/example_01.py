from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator


class AlertSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class AlertStatus(str, Enum):
    FIRING = "firing"
    RESOLVED = "resolved"


class AlertmanagerAlert(BaseModel):
    status: AlertStatus
    labels: dict[str, str]
    annotations: dict[str, str] = Field(default_factory=dict)
    starts_at: datetime = Field(alias="startsAt")
    ends_at: datetime | None = Field(default=None, alias="endsAt")
    generator_url: str = Field(default="", alias="generatorURL")
    fingerprint: str = Field(min_length=8, max_length=128)

    @field_validator("labels")
    @classmethod
    def require_core_labels(cls, value: dict[str, str]) -> dict[str, str]:
        required = {"alertname", "service", "namespace"}
        missing = required - set(value.keys())
        if missing:
            raise ValueError(f"Missing required Alertmanager labels: {sorted(missing)}")
        return value


class AlertmanagerWebhook(BaseModel):
    version: str = "4"
    group_key: str = Field(alias="groupKey")
    status: AlertStatus
    receiver: str
    alerts: list[AlertmanagerAlert] = Field(min_length=1)


class IncidentEnvelope(BaseModel):
    incident_id: str
    service: str
    namespace: str
    severity: AlertSeverity
    primary_alert: str
    alert_count: int = Field(ge=1)
    first_seen_utc: datetime
    dedup_key: str
    raw_labels: dict[str, str]

    @model_validator(mode="after")
    def validate_utc_timestamps(self) -> IncidentEnvelope:
        if self.first_seen_utc.tzinfo is None:
            self.first_seen_utc = self.first_seen_utc.replace(tzinfo=timezone.utc)
        return self


def build_incident_envelope(payload: dict[str, Any]) -> IncidentEnvelope:
    webhook = AlertmanagerWebhook.model_validate(payload)
    firing = [a for a in webhook.alerts if a.status == AlertStatus.FIRING]
    selected = firing[0] if firing else webhook.alerts[0]

    severity_raw = selected.labels.get("severity", "warning").lower()
    severity = AlertSeverity(severity_raw) if severity_raw in AlertSeverity._value2member_map_ else AlertSeverity.WARNING

    earliest = min(a.starts_at for a in webhook.alerts)
    service = selected.labels["service"]
    namespace = selected.labels["namespace"]
    dedup_material = f"{namespace}:{service}:{selected.labels['alertname']}:{earliest.strftime('%Y%m%d%H')}"
    dedup_key = hashlib.sha256(dedup_material.encode("utf-8")).hexdigest()[:16]

    return IncidentEnvelope(
        incident_id=f"INC-{dedup_key.upper()}",
        service=service,
        namespace=namespace,
        severity=severity,
        primary_alert=selected.labels["alertname"],
        alert_count=len(webhook.alerts),
        first_seen_utc=earliest,
        dedup_key=dedup_key,
        raw_labels=selected.labels,
    )


if __name__ == "__main__":
    sample_webhook = {
        "version": "4",
        "groupKey": "{}:{namespace=\"prod-payments\", service=\"checkout-orchestrator\"}",
        "status": "firing",
        "receiver": "triage-agent-webhook",
        "alerts": [
            {
                "status": "firing",
                "labels": {
                    "alertname": "KubePodCrashLooping",
                    "service": "checkout-orchestrator",
                    "namespace": "prod-payments",
                    "severity": "critical",
                },
                "annotations": {"summary": "Pod checkout-orchestrator-7d9b restarting repeatedly"},
                "startsAt": "2026-11-25T02:14:11Z",
                "fingerprint": "a84f91e0c1129b44",
            },
            {
                "status": "firing",
                "labels": {
                    "alertname": "HighHTTPLatencyP99",
                    "service": "checkout-orchestrator",
                    "namespace": "prod-payments",
                    "severity": "critical",
                },
                "startsAt": "2026-11-25T02:14:29Z",
                "fingerprint": "b29c01d8f4412a10",
            },
        ],
    }
    envelope = build_incident_envelope(sample_webhook)
    print(envelope.model_dump_json(indent=2))
