from dataclasses import dataclass, field
from enum import Enum

class Role(str, Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"

@dataclass
class Message:
    role: Role
    content: str
    tokens: int = field(init=False)
    pinned: bool = False

    def __post_init__(self):
        self.tokens = max(1, len(self.content) // 4)

class ContextGovernor:
    def __init__(self, max_token_budget: int = 4096, reserve_ratio: float = 0.25):
        self.max_budget = max_token_budget
        self.response_reserve = int(max_token_budget * reserve_ratio)
        self.usable_budget = max_token_budget - self.response_reserve
        self.history: List[Message] = []

    def add_message(self, role: Role, content: str, pinned: bool = False):
        msg = Message(role=role, content=content, pinned=pinned)
        self.history.append(msg)
        self._enforce_budget()

    def get_total_tokens(self) -> int:
        return sum(m.tokens for m in self.history)

    def _enforce_budget(self):
        while self.get_total_tokens() > self.usable_budget:
            evict_index = None
            for idx, msg in enumerate(self.history):
                if not msg.pinned and msg.role != Role.SYSTEM:
                    evict_index = idx
                    break
            
            if evict_index is None:
                break
            
            evicted = self.history.pop(evict_index)
            if not any("Prior history compacted" in m.content for m in self.history):
                summary_msg = Message(
                    role=Role.SYSTEM,
                    content="[System: Prior history compacted to conserve context window]",
                    pinned=False
                )
                self.history.insert(evict_index, summary_msg)

    def export_context(self) -> List[Dict[str, str]]:
        return [{"role": m.role.value, "content": m.content} for m in self.history]

# Verification of Recipe 1.3
governor = ContextGovernor(max_token_budget=500, reserve_ratio=0.20)
governor.add_message(Role.SYSTEM, "You are a hardened financial fraud agent.", pinned=True)
governor.add_message(Role.USER, "Investigate transaction TX-9012 for potential money laundering.", pinned=False)

for step in range(1, 8):
    governor.add_message(
        Role.TOOL, 
        f"Step {step}: Checked ledger database. Returned 24 records of transfer history with SHA-256 hashes.",
        pinned=False
    )

print(f"Total Active Tokens: {governor.get_total_tokens()} / {governor.usable_budget}")
print(f"Message Count post-compaction: {len(governor.history)}")
