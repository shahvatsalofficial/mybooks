from __future__ import annotations

import hashlib


def compute_dedup_key(namespace: str, service: str, alertname: str, hour_bucket: str) -> str:
    material = f"{namespace}:{service}:{alertname}:{hour_bucket}"
    return hashlib.sha256(material.encode("utf-8")).hexdigest()[:16]


if __name__ == "__main__":
    k1 = compute_dedup_key("prod-payments", "checkout-orchestrator", "KubePodCrashLooping", "2026112502")
    k2 = compute_dedup_key("prod-payments", "checkout-orchestrator", "KubePodCrashLooping", "2026112502")
    k3 = compute_dedup_key("prod-payments", "checkout-orchestrator", "HighHTTPLatencyP99", "2026112502")
    assert k1 == k2, "Same alert in same hour must coalesce"
    assert k1 != k3, "Distinct alertnames must not collide"
    print(f"PASS: k1==k2 ({k1}) and k1!=k3 ({k3})")
