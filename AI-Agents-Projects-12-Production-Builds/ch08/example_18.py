from __future__ import annotations

import re

PRIVATE_IPV4_RE = re.compile(
    r"\b(?:10\.\d{1,3}\.\d{1,3}\.\d{1,3}|192\.168\.\d{1,3}\.\d{1,3})\b"
)


def redact_private_ips(text: str) -> str:
    return PRIVATE_IPV4_RE.sub("[REDACTED_INTERNAL_IP]", text)


if __name__ == "__main__":
    print(redact_private_ips("DB host moved to 10.24.18.92 and 192.168.1.15."))
