import asyncio
from typing import AsyncGenerator, Dict, Any

class StreamingToolRunner:
    async def run_long_tool(self, tool_name: str, total_chunks: int = 4) -> AsyncGenerator[Dict[str, Any], None]:
        for i in range(1, total_chunks + 1):
            await asyncio.sleep(0.01)
            pct = int((i / total_chunks) * 100)
            yield {
                "tool": tool_name,
                "progress_pct": pct,
                "status": "RUNNING" if i < total_chunks else "COMPLETED",
                "delta": f"Processed batch {i}/{total_chunks}"
            }

async def consume_deltas():
    runner = StreamingToolRunner()
    async for event in runner.run_long_tool("index_codebase", 4):
        print(f"[TOOL STREAM] {event['tool']} -> {event['progress_pct']}%: {event['delta']}")

asyncio.run(consume_deltas())
