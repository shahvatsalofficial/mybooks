from __future__ import annotations

import asyncio
import time
from pydantic import BaseModel, Field


class FirmographicProfile(BaseModel):
    domain: str
    employee_count: int = Field(ge=1)
    annual_revenue_usd_m: float = Field(ge=0.0)
    industry: str
    tech_stack: list[str]
    verified_facts: list[str]
    cached: bool = False


class EnrichmentFanOutEngine:
    def __init__(self, cache_ttl_sec: float = 604_800.0) -> None:
        self.cache_ttl_sec = cache_ttl_sec
        self._cache: dict[str, tuple[float, FirmographicProfile]] = {}

    async def _fetch_clearbit(self, domain: str) -> dict[str, object]:
        await asyncio.sleep(0.02)
        return {"employees": 640, "revenue_m": 82.5, "industry": "B2B Cloud Infrastructure"}

    async def _fetch_technographics(self, domain: str) -> list[str]:
        await asyncio.sleep(0.015)
        return ["Kubernetes", "Terraform", "Snowflake", "Salesforce"]

    async def _fetch_verified_news(self, domain: str) -> list[str]:
        await asyncio.sleep(0.018)
        return [
            "Published SOC2 Type II attestation in Q3 2026",
            "Migrated core billing cluster to multi-region Kubernetes",
        ]

    async def enrich(self, domain: str) -> FirmographicProfile:
        now = time.monotonic()
        if domain in self._cache:
            ts, profile = self._cache[domain]
            if (now - ts) < self.cache_ttl_sec:
                return profile.model_copy(update={"cached": True})

        firm_task = asyncio.wait_for(self._fetch_clearbit(domain), timeout=1.5)
        tech_task = asyncio.wait_for(self._fetch_technographics(domain), timeout=1.5)
        news_task = asyncio.wait_for(self._fetch_verified_news(domain), timeout=1.5)

        firm, tech, news = await asyncio.gather(firm_task, tech_task, news_task)
        profile = FirmographicProfile(
            domain=domain,
            employee_count=int(firm["employees"]),
            annual_revenue_usd_m=float(firm["revenue_m"]),
            industry=str(firm["industry"]),
            tech_stack=tech,
            verified_facts=news,
            cached=False,
        )
        self._cache[domain] = (now, profile)
        return profile


async def main() -> None:
    engine = EnrichmentFanOutEngine()
    first = await engine.enrich("acme-cloud.co.uk")
    second = await engine.enrich("acme-cloud.co.uk")
    print("First call cached=", first.cached, "employees=", first.employee_count, "facts=", len(first.verified_facts))
    print("Second call cached=", second.cached, "stack=", second.tech_stack)


if __name__ == "__main__":
    asyncio.run(main())
