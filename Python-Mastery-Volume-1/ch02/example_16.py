from typing import AsyncGenerator, AsyncIterable

async def stream_financial_ticks(symbol: str) -> AsyncGenerator[float, None]:
    """Asynchronous generator yielding live tick prices."""
    while True:
        price = await fetch_live_price(symbol)
        if price is None:
            break
        yield price

async def aggregate_volume(stream: AsyncIterable[float]) -> float:
    """Accepts any compatible asynchronous stream, decoupled from concrete generator."""
    total = 0.0
    async for tick in stream:
        total += tick
    return total
