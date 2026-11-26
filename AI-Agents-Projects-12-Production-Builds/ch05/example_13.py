from __future__ import annotations

import re

SECRET_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("BEARER_TOKEN", re.compile(r"Bearer\s+[A-Za-z0-9\-._~+/]+=*", re.IGNORECASE)),
    ("PG_DSN", re.compile(r"postgres(?:ql)?://[^:\s]+:[^@\s]+@[^\s]+", re.IGNORECASE)),
    ("AWS_KEY", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("EMAIL", re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")),
]


def redact_sensitive_text(raw_text: str) -> tuple[str, dict[str, int]]:
    redacted = raw_text
    counts: dict[str, int] = {}
    for label, pattern in SECRET_PATTERNS:
        redacted, hits = pattern.subn(f"[REDACTED_{label}]", redacted)
        if hits > 0:
            counts[label] = hits
    return redacted, counts


if __name__ == "__main__":
    dirty_log = (
        "2026-11-25T02:14:15Z ERROR auth_failed user=alice@example.com "
        "dsn=postgresql://app_user:Sup3rS3cret!@pg-prod:5432/orders header='Bearer eyJhbGciOiJIUzI1NiJ9.abc.xyz'"
    )
    clean_log, stats = redact_sensitive_text(dirty_log)
    print("Clean:", clean_log)
    print("Redactions:", stats)
