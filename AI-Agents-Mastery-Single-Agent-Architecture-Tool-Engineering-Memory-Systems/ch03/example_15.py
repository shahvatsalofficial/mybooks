from typing import Dict, Any

class ToolOutputCompactor:
    def __init__(self, max_allowed_tokens: int = 500):
        self.max_tokens = max_allowed_tokens

    def compact(self, raw_tool_result: str) -> str:
        words = raw_tool_result.split()
        if len(words) <= self.max_tokens:
            return raw_tool_result

        # Retain head and tail for debugging context
        head_count = int(self.max_tokens * 0.6)
        tail_count = int(self.max_tokens * 0.4)
        omitted = len(words) - (head_count + tail_count)

        compacted = " ".join(words[:head_count])
        compacted += f"\n\n[... WARNING: {omitted} intermediate words truncated by Token Compactor ...]\n\n"
        compacted += " ".join(words[-tail_count:])
        return compacted

compactor = ToolOutputCompactor(max_allowed_tokens=20)
raw = "error " * 100
summary = compactor.compact(raw)
print("Compacted Tool Payload:\n", summary)
