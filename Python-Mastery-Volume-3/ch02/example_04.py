import asyncio
from collections.abc import AsyncGenerator
from fastapi import FastAPI
from fastapi.responses import StreamingResponse

app = FastAPI()

async def event_publisher() -> AsyncGenerator[str, None]:
    """Asynchronous generator yielding formatted SSE data packets."""
    for seq in range(1, 100):
        # Cooperatively sleep to simulate real-time event generation
        await asyncio.sleep(0.05)
        # Yield standard SSE protocol wire format: "data: <payload>\n\n"
        yield f"event: telemetry\nid: {seq}\ndata: {{\"metric_id\": {seq}, \"value\": {seq * 1.5}}}\n\n"

@app.get("/api/v1/telemetry/stream")
async def stream_telemetry() -> StreamingResponse:
    return StreamingResponse(
        event_publisher(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disables proxy buffering in NGINX
        },
    )
