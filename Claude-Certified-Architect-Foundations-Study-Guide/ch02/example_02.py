import asyncio
import os
import anthropic

MODEL = "claude-sonnet-4-20250514"


async def audit_one(
    client: anthropic.AsyncAnthropic, sem: asyncio.Semaphore, service: str
) -> str:
    async with sem:
        resp = await client.messages.create(
            model=MODEL,
            max_tokens=200,
            system="Summarize service health in 1 sentence.",
            messages=[{"role": "user", "content": f"Scoped Brief: Audit {service}."}],
        )
        text = "".join(b.text for b in resp.content if b.type == "text").strip()
        return f"{service}: {text}"


async def gather_service_audits(services: list[str]) -> list[str]:
    client = anthropic.AsyncAnthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    sem = asyncio.Semaphore(3)
    tasks = [audit_one(client, sem, svc) for svc in services]
    return await asyncio.gather(*tasks)
