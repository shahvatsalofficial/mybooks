"""
Resilient Async SSE Stream Consumer with Cancellation Propagation
Guarantees clean socket closure and zero orphan stream consumption.
"""
import asyncio
import logging
from typing import AsyncGenerator
from openai import AsyncOpenAI

logger = logging.getLogger("stream_governor")

async def resilient_token_stream(
    client: AsyncOpenAI,
    model: str,
    prompt: str,
    abort_event: asyncio.Event
) -> AsyncGenerator[str, None]:
    stream_response = await client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        stream=True,
        stream_options={"include_usage": True}
    )
    
    try:
        async for chunk in stream_response:
            if abort_event.is_set():
                logger.warning("Downstream consumer cancelled. Propagating abort to upstream stream.")
                break
                
            if chunk.choices and len(chunk.choices) > 0:
                delta_content = chunk.choices[0].delta.content
                if delta_content:
                    yield delta_content
                    
            if chunk.usage:
                logger.info(f"Verified Stream Usage: {chunk.usage.total_tokens} total tokens.")
                
    except asyncio.CancelledError:
        logger.warning("Task execution cancelled externally. Cleaning up stream socket.")
        raise
    finally:
        # Crucial: Explicitly close the underlying async HTTP response stream
        await stream_response.response.aclose()
