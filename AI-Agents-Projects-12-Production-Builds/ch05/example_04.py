from __future__ import annotations

from datetime import datetime, timezone
from pydantic import BaseModel, Field


class GitCommitRecord(BaseModel):
    sha: str = Field(min_length=7, max_length=40)
    author: str
    message: str
    deployed_at: datetime
    changed_files: list[str]
    rollback_target_sha: str


class CommitCorrelationScore(BaseModel):
    sha: str
    minutes_before_incident: float
    risk_score: float = Field(ge=0.0, le=1.0)
    matched_risk_paths: list[str]
    rollback_target_sha: str


HIGH_RISK_PATTERNS = ("migrations/", "db/", "pool", "helm/", "k8s/", "config/", "timeout")


def score_recent_commits(
    commits: list[GitCommitRecord],
    incident_time: datetime,
    lookback_minutes: float = 120.0,
) -> list[CommitCorrelationScore]:
    if incident_time.tzinfo is None:
        incident_time = incident_time.replace(tzinfo=timezone.utc)

    scored: list[CommitCorrelationScore] = []
    for commit in commits:
        dep_time = commit.deployed_at.replace(tzinfo=timezone.utc) if commit.deployed_at.tzinfo is None else commit.deployed_at
        delta_min = (incident_time - dep_time).total_seconds() / 60.0
        if delta_min < 0 or delta_min > lookback_minutes:
            continue

        recency_weight = max(0.0, 1.0 - (delta_min / lookback_minutes))
        risk_paths = [f for f in commit.changed_files if any(pat in f.lower() for pat in HIGH_RISK_PATTERNS)]
        path_weight = min(1.0, len(risk_paths) * 0.25)
        combined = round(min(1.0, (0.65 * recency_weight) + (0.35 * path_weight)), 3)

        scored.append(
            CommitCorrelationScore(
                sha=commit.sha,
                minutes_before_incident=round(delta_min, 2),
                risk_score=combined,
                matched_risk_paths=risk_paths,
                rollback_target_sha=commit.rollback_target_sha,
            )
        )

    return sorted(scored, key=lambda c: c.risk_score, reverse=True)


if __name__ == "__main__":
    inc_time = datetime(2026, 11, 25, 2, 14, 11, tzinfo=timezone.utc)
    recent = [
        GitCommitRecord(
            sha="9f3a2c1",
            author="dev-platform-bot",
            message="feat(checkout): add order metadata JSONB filter",
            deployed_at=datetime(2026, 11, 25, 2, 9, 40, tzinfo=timezone.utc),
            changed_files=["src/checkout/queries.py", "migrations/20261125_order_meta.sql", "helm/values-prod.yaml"],
            rollback_target_sha="4b18e02",
        ),
        GitCommitRecord(
            sha="4b18e02",
            author="sre-release",
            message="docs: update runbook link",
            deployed_at=datetime(2026, 11, 25, 0, 45, 0, tzinfo=timezone.utc),
            changed_files=["README.md"],
            rollback_target_sha="1a09d44",
        ),
    ]
    for item in score_recent_commits(recent, inc_time):
        print(item.model_dump_json())
