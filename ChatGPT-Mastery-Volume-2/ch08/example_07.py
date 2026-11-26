"""
Enterprise Asynchronous Shadow Prompting Dispatcher
Mirrors live traffic to candidate models for zero-risk online evaluation.
Author: Vatsal Shah, Enterprise AI Architect
"""
import asyncio
import time
from typing import Dict, Any
from openai import AsyncOpenAI

client = AsyncOpenAI()

async def execute_shadow_evaluation(
    prompt: str,
    prod_completion: str,
    candidate_model: str = "ft:gpt-4o-mini:enterprise:v2"
):
    """Executes asynchronously in background; never delays primary user response."""
    start_time = time.time()
    try:
        candidate_resp = await client.chat.completions.create(
            model=candidate_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0
        )
        duration_ms = (time.time() - start_time) * 1000
        candidate_completion = candidate_resp.choices[0].message.content

        # Log dual outputs to analytics database for offline comparison
        print(f"📊 Shadow Eval Logged: Model={candidate_model} Latency={duration_ms:.1f}ms")
        # In production: write_to_clickhouse(prompt, prod_completion, candidate_completion, duration_ms)

    except Exception as exc:
        print(f"⚠️ Shadow evaluation failed non-critically: {exc}")

async def dispatch_with_shadow(
    prompt: str,
    prod_model: str = "gpt-4o",
    candidate_model: str = "gpt-4o-mini"
) -> str:
    # 1. Execute primary production call synchronously
    prod_resp = await client.chat.completions.create(
        model=prod_model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7
    )
    prod_text = prod_resp.choices[0].message.content

    # 2. Fire-and-forget shadow evaluation into event loop
    asyncio.create_task(
        execute_shadow_evaluation(prompt, prod_text, candidate_model)
    )

    # 3. Immediately return primary completion to waiting user
    return prod_text
