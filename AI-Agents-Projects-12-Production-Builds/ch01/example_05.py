from __future__ import annotations

import math
from datetime import datetime, timezone


AUTHORITY_RULES: dict[str, tuple[SourceTier, float]] = {
    ".gov": (SourceTier.PRIMARY_OFFICIAL, 0.98),
    ".edu": (SourceTier.PEER_REVIEWED, 0.90),
    "arxiv.org": (SourceTier.PEER_REVIEWED, 0.89),
    "ietf.org": (SourceTier.PRIMARY_OFFICIAL, 0.96),
    "docs.python.org": (SourceTier.PRIMARY_OFFICIAL, 0.95),
    "github.com": (SourceTier.ENGINEERING_BLOG, 0.82),
    "medium.com": (SourceTier.NEWS_AGGREGATOR, 0.55),
    "reddit.com": (SourceTier.UNVERIFIED_FORUM, 0.35),
}


def classify_domain(domain: str) -> tuple[SourceTier, float]:
    d = domain.lower().strip()
    for suffix_or_host, (tier, base_score) in AUTHORITY_RULES.items():
        if d == suffix_or_host or d.endswith(suffix_or_host):
            return tier, base_score
    if d.startswith("docs.") or d.startswith("developer."):
        return SourceTier.PRIMARY_OFFICIAL, 0.90
    return SourceTier.NEWS_AGGREGATOR, 0.52


def compute_freshness_decay(
    published_at: datetime | None,
    reference_now: datetime,
    half_life_days: float = 180.0,
) -> float:
    if published_at is None:
        return 0.65  # Conservative penalty when publication date is missing
    age_days = max(0.0, (reference_now - published_at).total_seconds() / 86400.0)
    return math.exp(-math.log(2.0) * (age_days / half_life_days))


def compute_source_trust(
    domain: str,
    published_at: datetime | None,
    reference_now: datetime | None = None,
) -> tuple[SourceTier, float]:
    now = reference_now or datetime.now(timezone.utc)
    tier, auth = classify_domain(domain)
    freshness = compute_freshness_decay(published_at, now)
    composite = round((0.70 * auth) + (0.30 * freshness), 4)
    return tier, composite


if __name__ == "__main__":
    ref = datetime(2026, 6, 1, tzinfo=timezone.utc)
    candidates = [
        ("nist.gov", datetime(2026, 4, 15, tzinfo=timezone.utc)),
        ("docs.kubernetes.io", datetime(2025, 11, 1, tzinfo=timezone.utc)),
        ("medium.com", datetime(2024, 1, 10, tzinfo=timezone.utc)),
        ("reddit.com", None),
    ]
    for dom, pub in candidates:
        tier, score = compute_source_trust(dom, pub, ref)
        print(f"domain={dom:<20} tier={tier.value:<18} trust={score:.4f}")
