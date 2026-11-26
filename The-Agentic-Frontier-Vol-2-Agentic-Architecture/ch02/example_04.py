import re
import json

def self_healing_json_parse(raw_text: str) -> dict:
    """Parses malformed LLM JSON outputs via multi-stage deterministic regex repair."""
    # Stage 1: Fast direct load
    try:
        return json.loads(raw_text)
    except Exception:
        pass

    # Stage 2: Extract code block
    fence_match = re.search(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", raw_text)
    cleaned = fence_match.group(1) if fence_match else raw_text.strip()

    # Stage 3: Repair trailing commas and unescaped newlines
    cleaned = re.sub(r",\s*([\}\]])", r"\1", cleaned)
    cleaned = cleaned.replace("\n", " ").replace("\r", "")

    # Stage 4: Attempt re-parse
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as err:
        raise ValueError(f"JSON repair failed at character {err.pos}: {err.msg}")
