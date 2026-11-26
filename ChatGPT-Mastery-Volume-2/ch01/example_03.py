"""
Zero-Latency Local Token Budget Auditor
Enforces strict pre-flight token caps across complex multi-message payloads.
"""
from typing import List, Dict, Any
import tiktoken

class TokenBudgetAuditor:
    def __init__(self, model_name: str = "gpt-4o"):
        self.model_name = model_name
        try:
            self.encoding = tiktoken.encoding_for_model(model_name)
        except KeyError:
            self.encoding = tiktoken.get_encoding("o200k_base")
            
        # Message envelope formatting overhead (OpenAI ChatML formatting)
        self.tokens_per_message = 3
        self.tokens_per_name = 1
        self.reply_priming_tokens = 3

    def calculate_messages_tokens(self, messages: List[Dict[str, Any]]) -> int:
        total_tokens = 0
        for message in messages:
            total_tokens += self.tokens_per_message
            for key, value in message.items():
                if isinstance(value, str):
                    total_tokens += len(self.encoding.encode(value))
                if key == "name":
                    total_tokens += self.tokens_per_name
        total_tokens += self.reply_priming_tokens
        return total_tokens

    def enforce_ceiling(self, messages: List[Dict[str, Any]], max_tokens_allowed: int) -> bool:
        projected = self.calculate_messages_tokens(messages)
        if projected > max_tokens_allowed:
            raise ValueError(
                f"PAYLOAD REJECTED: Projected tokens ({projected}) exceeds budget ceiling ({max_tokens_allowed})."
            )
        return True
