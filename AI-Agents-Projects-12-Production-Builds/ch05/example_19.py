from __future__ import annotations

import asyncio
from collections import defaultdict


async def coalesce_alert_storm(events: list[tuple[str, str, str]]) -> dict[tuple[str, str], list[str]]:
    await asyncio.sleep(0.05)
    grouped: dict[tuple[str, str], list[str]] = defaultdict(list)
    for namespace, service, alertname in events:
        grouped[(namespace, service)].append(alertname)
    return dict(grouped)


async def main() -> None:
    storm = [
        ("prod-payments", "checkout-orchestrator", "KubePodCrashLooping"),
        ("prod-payments", "checkout-orchestrator", "HighHTTPLatencyP99"),
        ("prod-payments", "checkout-orchestrator", "ReadinessProbeFailed"),
        ("prod-orders", "order-writer", "HighDBConnections"),
    ]
    batched = await coalesce_alert_storm(storm)
    for svc_key, alerts in batched.items():
        print(f"{svc_key}: {len(alerts)} alerts -> {alerts}")


if __name__ == "__main__":
    asyncio.run(main())
