import json
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from anthropic import Anthropic

class ChatMessage(BaseModel):
    role: str = Field(..., pattern="^(user|assistant)$")
    content: str
    token_estimate: int = 0

class ManagedConversationBuffer:
    def __init__(
        self,
        api_key: str,
        system_prompt: str,
        max_verbatim_turns: int = 6,
        max_total_tokens: int = 8000
    ):
        self.client = Anthropic(api_key=api_key)
        self.system_prompt = system_prompt
        self.max_turns = max_verbatim_turns
        self.max_tokens = max_total_tokens
        self.verbatim_history: List[ChatMessage] = []
        self.running_memory_summary: str = ""

    def _estimate_tokens(self, text: str) -> int:
        return len(text) // 4 + 1  # Fast conservative heuristic

    def _compact_older_history(self, evicted_messages: List[ChatMessage]):
        """Compresses evicted dialogue into cumulative state summary."""
        evicted_text = "\n".join([f"{m.role.upper()}: {m.content}" for m in evicted_messages])
        
        prompt = (
            f"CURRENT RUNNING STATE SUMMARY:\n{self.running_memory_summary or 'None'}\n\n"
            f"NEW CONVERSATIONAL TURNS TO COMPACT:\n{evicted_text}\n\n"
            "Update the running state summary. Retain all user constraints, business decisions, "
            "technical parameters, and active task state. Be terse and factual."
        )

        res = self.client.messages.create(
            model="claude-3-5-haiku-20241022",
            max_tokens=600,
            temperature=0.0,
            system="You are an Enterprise State Compactor. Maintain high factual density.",
            messages=[{"role": "user", "content": prompt}]
        )
        self.running_memory_summary = res.content[0].text.strip()

    def add_turn(self, role: str, content: str):
        tokens = self._estimate_tokens(content)
        msg = ChatMessage(role=role, content=content, token_estimate=tokens)
        self.verbatim_history.append(msg)

        # Evict older turns if turn count exceeds threshold
        if len(self.verbatim_history) > self.max_turns:
            evicted = self.verbatim_history[:-self.max_turns]
            self.verbatim_history = self.verbatim_history[-self.max_turns:]
            self._compact_older_history(evicted)

    def assemble_payload(self) -> List[Dict[str, str]]:
        messages = []

        # Inject compacted memory block if present
        if self.running_memory_summary:
            memory_block = (
                f"<compacted_historical_context>\n"
                f"{self.running_memory_summary}\n"
                f"</compacted_historical_context>"
            )
            # Prepend memory block into the oldest active user turn
            if self.verbatim_history and self.verbatim_history[0].role == "user":
                first_msg = self.verbatim_history[0]
                messages.append({
                    "role": "user",
                    "content": f"{memory_block}\n\n{first_msg.content}"
                })
                # Add remainder
                for m in self.verbatim_history[1:]:
                    messages.append({"role": m.role, "content": m.content})
                return messages

        for m in self.verbatim_history:
            messages.append({"role": m.role, "content": m.content})
        return messages
