from __future__ import annotations

import hashlib
import re
from collections import Counter
from typing import Iterable

from pydantic import BaseModel

UUID_RE = re.compile(r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b")
IPV4_RE = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
HEX_RE = re.compile(r"\b0x[0-9a-fA-F]+\b")
NUM_RE = re.compile(r"\b\d+\b")


class LogSignature(BaseModel):
    signature_id: str
    template: str
    occurrences: int
    sample_line: str


def normalize_log_line(line: str) -> str:
    masked = UUID_RE.sub("<UUID>", line)
    masked = IPV4_RE.sub("<IP>", masked)
    masked = HEX_RE.sub("<HEX>", masked)
    masked = NUM_RE.sub("<NUM>", masked)
    return " ".join(masked.split())


def aggregate_loki_streams(lines: Iterable[str], top_k: int = 5) -> list[LogSignature]:
    counts: Counter[str] = Counter()
    samples: dict[str, str] = {}

    for raw in lines:
        cleaned = raw.strip()
        if not cleaned:
            continue
        template = normalize_log_line(cleaned)
        counts[template] += 1
        samples.setdefault(template, cleaned)

    results: list[LogSignature] = []
    for template, occurrences in counts.most_common(top_k):
        sig_id = hashlib.sha1(template.encode("utf-8")).hexdigest()[:12]
        results.append(
            LogSignature(
                signature_id=sig_id,
                template=template,
                occurrences=occurrences,
                sample_line=samples[template],
            )
        )
    return results


if __name__ == "__main__":
    raw_loki_lines = [
        "ERROR db_pool exhausted req=550e8400-e29b-41d4-a716-446655440000 host=10.42.8.19 wait_ms=5002",
        "ERROR db_pool exhausted req=660e8400-e29b-41d4-a716-446655440011 host=10.42.8.22 wait_ms=5014",
        "ERROR db_pool exhausted req=770e8400-e29b-41d4-a716-446655440099 host=10.42.8.14 wait_ms=5008",
        "WARN retry_budget_low downstream=redis-cluster attempt=3",
        "ERROR db_pool exhausted req=880e8400-e29b-41d4-a716-446655440123 host=10.42.8.19 wait_ms=5031",
    ]
    for sig in aggregate_loki_streams(raw_loki_lines):
        print(sig.model_dump_json())
