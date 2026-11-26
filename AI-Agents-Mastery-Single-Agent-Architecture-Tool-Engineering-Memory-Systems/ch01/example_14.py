import asyncio
import json
from typing import AsyncGenerator, Dict, Any

async def mock_llm_stream() -> AsyncGenerator[str, None]:
    chunks = [
        '{"thought": "User wants',
        ' account balance.", "action":',
        ' "get_balance", "parameters":',
        ' {"account_id": "ACC-99',
        '10", "currency": "USD"}}'
    ]
    for c in chunks:
        await asyncio.sleep(0.01)
        yield c

class StreamingActionParser:
    def __init__(self):
        self.buffer = ""

    async def parse_stream(self, stream: AsyncGenerator[str, None]) -> Dict[str, Any]:
        async for chunk in stream:
            self.buffer += chunk
            try:
                parsed = json.loads(self.buffer)
                if "action" in parsed and "parameters" in parsed:
                    return parsed
            except json.JSONDecodeError:
                continue
        raise ValueError("Stream ended without valid JSON payload")

async def run_streaming_pipeline():
    parser = StreamingActionParser()
    result = await parser.parse_stream(mock_llm_stream())
    print("Action Extracted in Real-Time:", result["action"], result["parameters"])

asyncio.run(run_streaming_pipeline())
