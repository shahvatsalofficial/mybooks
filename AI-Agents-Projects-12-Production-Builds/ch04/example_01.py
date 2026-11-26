from __future__ import annotations

import asyncio
import time
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class FilingMetadata(BaseModel):
    cik: str
    company_name: str
    form_type: str
    accession_number: str
    filing_date: str
    report_date: str
    is_amendment: bool = False


class AsyncTokenBucket:
    """Enforces SEC EDGAR's 10 requests/second rate limit with safety margin."""

    def __init__(self, rate_per_sec: float = 8.0) -> None:
        self._interval = 1.0 / rate_per_sec
        self._last_call = 0.0
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        async with self._lock:
            now = time.monotonic()
            wait_s = self._interval - (now - self._last_call)
            if wait_s > 0:
                await asyncio.sleep(wait_s)
            self._last_call = time.monotonic()


class EdgarClient:
    """Compliant SEC EDGAR metadata and XBRL CompanyFacts client."""

    def __init__(self, user_agent: str, rate_per_sec: float = 8.0) -> None:
        if "@" not in user_agent or " " not in user_agent.strip():
            raise ValueError("SEC EDGAR requires User-Agent: 'OrgName contact@domain.com'")
        self._headers = {"User-Agent": user_agent, "Accept-Encoding": "gzip, deflate"}
        self._bucket = AsyncTokenBucket(rate_per_sec=rate_per_sec)

    @staticmethod
    def pad_cik(cik: str | int) -> str:
        digits = "".join(ch for ch in str(cik) if ch.isdigit())
        if not digits:
            raise ValueError(f"Invalid CIK: {cik}")
        return digits.zfill(10)

    async def fetch_recent_filings(
        self, cik: str | int, forms: Optional[List[str]] = None
    ) -> List[FilingMetadata]:
        await self._bucket.acquire()
        padded = self.pad_cik(cik)
        target_forms = set(forms or ["10-K", "10-K/A", "10-Q"])

        # Deterministic offline-safe payload matching SEC submissions JSON schema
        simulated_submissions: Dict[str, Any] = {
            "cik": padded,
            "name": "Apex Semiconductor Corp",
            "filings": {
                "recent": {
                    "form": ["10-K", "10-Q", "8-K"],
                    "accessionNumber": ["0000950170-26-014210", "0000950170-26-008112", "0000950170-26-004001"],
                    "filingDate": ["2026-02-18", "2025-11-04", "2025-09-12"],
                    "reportDate": ["2025-12-31", "2025-09-30", "2025-09-10"],
                }
            },
        }
        recent = simulated_submissions["filings"]["recent"]
        results: List[FilingMetadata] = []
        for idx, form in enumerate(recent["form"]):
            if form in target_forms:
                results.append(
                    FilingMetadata(
                        cik=padded,
                        company_name=simulated_submissions["name"],
                        form_type=form,
                        accession_number=recent["accessionNumber"][idx],
                        filing_date=recent["filingDate"][idx],
                        report_date=recent["reportDate"][idx],
                        is_amendment=form.endswith("/A"),
                    )
                )
        return results


async def main() -> None:
    client = EdgarClient(user_agent="Opportunity4uResearch compliance@opportunity4u.io")
    filings = await client.fetch_recent_filings("950170", forms=["10-K", "10-Q"])
    for f in filings:
        print(f.model_dump_json())


if __name__ == "__main__":
    asyncio.run(main())
