import asyncio
from typing import AsyncGenerator

async def stream_azure_agent_turn(prompt: str) -> AsyncGenerator[str, None]:
    """Asynchronous generator emitting real-time agent output chunks."""
    simulated_chunks = [
        "Analyzing ", "Azure ", "resource ", "health...\n",
        "- Resource: vm-payment-processor-01\n",
        "- Status: Degraded (CPU saturation at 98.4%)\n",
        "Action: Triggering automated VM horizontal scaling rule."
    ]
    for chunk in simulated_chunks:
        await asyncio.sleep(0.04)
        yield chunk

async def test_runner():
    print("Starting Azure agent stream:")
    async for token in stream_azure_agent_turn("Diagnose payment processor"):
        print(token, end="", flush=True)
    print("\nStream finished.")

if __name__ == "__main__":
    asyncio.run(test_runner())
