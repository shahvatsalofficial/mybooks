"""
recipe_5_4_resilient_sampling.py
Python MCP server with dynamic capability detection and heuristic fallback.
"""

import sys
from mcp.server.fastmcp import FastMCP, Context
from mcp.types import CreateMessageResult

server = FastMCP("ResilientSamplingServer")


def fallback_extractive_summary(text: str, max_sentences: int = 2) -> str:
    """Deterministic fallback summarizer when sampling is unavailable."""
    sentences = [s.strip() for s in text.split(".") if len(s.strip()) > 10]
    return ". ".join(sentences[:max_sentences]) + "."


@server.tool(
    name="extract_meeting_action_items",
    description="Extracts key action items from transcript text using sampling with heuristic fallback."
)
async def extract_meeting_action_items(transcript: str, ctx: Context) -> str:
    """Uses reverse sampling if supported by client; otherwise falls back to heuristics."""
    sys.stderr.write("[Server] Received action item extraction request.\n")

    # Attempt reverse sampling via the host session
    try:
        sys.stderr.write("[Server] Dispatching sampling/createMessage to host...\n")
        response: CreateMessageResult = await ctx.session.create_message(
            messages=[
                {
                    "role": "user",
                    "content": {
                        "type": "text",
                        "text": f"Extract all action items with owners from this transcript:\n\n{transcript}"
                    }
                }
            ],
            system_prompt="You are an executive assistant. Output a concise markdown checklist.",
            max_tokens=300,
            temperature=0.2
        )

        if response.content.type == "text":
            return f"### Action Items (Generated via {response.model})\n\n{response.content.text}"

    except Exception as exc:
        sys.stderr.write(f"[Server Warning] Host sampling failed or not supported: {exc}\n")
        sys.stderr.write("[Server] Engaging fallback extractive heuristic...\n")

    # Fallback execution path
    summary = fallback_extractive_summary(transcript)
    return (
        f"### Action Items (Extracted via Local Heuristic Fallback)\n\n"
        f"*(Note: Host LLM sampling unavailable)*\n\n"
        f"- {summary}"
    )


if __name__ == "__main__":
    server.run(transport="stdio")
