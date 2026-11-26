# finops_telemetry_exporter.py — Real-Time Billing & Usage Dispatcher
import aiohttp
import json
import time

class FinOpsTelemetryExporter:
    """Streams token usage events to enterprise cost ledgers."""
    def __init__(self, ingest_endpoint: str, api_key: str):
        self.endpoint = ingest_endpoint
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

    async def record_usage(
        self,
        tenant_id: str,
        department: str,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        duration_ms: float
    ):
        # Calculate pricing tiers ($ USD)
        prices = {
            "gpt-4o": {"in": 0.0000025, "out": 0.0000100},
            "gpt-4o-mini": {"in": 0.00000015, "out": 0.00000060},
            "o3-mini": {"in": 0.0000011, "out": 0.0000044}
        }
        tier = prices.get(model, prices["gpt-4o"])
        cost = (prompt_tokens * tier["in"]) + (completion_tokens * tier["out"])

        payload = {
            "timestamp": int(time.time()),
            "tenant_id": tenant_id,
            "department": department,
            "model": model,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens,
            "estimated_cost_usd": round(cost, 6),
            "duration_ms": duration_ms
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(self.endpoint, headers=self.headers, json=payload) as resp:
                if resp.status != 200:
                    print(f"Warning: Telemetry failed with status {resp.status}")
