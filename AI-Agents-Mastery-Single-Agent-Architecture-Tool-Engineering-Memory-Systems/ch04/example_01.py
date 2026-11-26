import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set

@dataclass
class MemoryItem:
    role: str
    content: str
    turn: int
    is_pinned: bool = False
    tokens: int = field(init=False)

    def __post_init__(self):
        self.tokens = max(1, len(self.content) // 4)

class EntityPreservingBuffer:
    def __init__(self, token_limit: int = 2048):
        self.token_limit = token_limit
        self.items: List[MemoryItem] = []
        self.current_turn = 0
        # Regex to detect persistent entities (IDs, emails, currencies)
        self.entity_pattern = re.compile(r"(ORD-\d+|CUST-\d+|USR-\d+|[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)")

    def add(self, role: str, content: str):
        self.current_turn += 1
        # Automatically pin system prompts or messages containing critical entities
        has_entities = bool(self.entity_pattern.search(content))
        should_pin = (role.lower() == "system") or has_entities
        
        item = MemoryItem(
            role=role, 
            content=content, 
            turn=self.current_turn, 
            is_pinned=should_pin
        )
        self.items.append(item)
        self._enforce_bounds()

    def get_total_tokens(self) -> int:
        return sum(i.tokens for i in self.items)

    def _enforce_bounds(self):
        while self.get_total_tokens() > self.token_limit:
            evict_idx = None
            # Scan from oldest for unpinned items
            for idx, item in enumerate(self.items):
                if not item.is_pinned:
                    evict_idx = idx
                    break
            
            if evict_idx is None:
                # All messages are pinned; cannot evict further without losing entities
                break
            
            self.items.pop(evict_idx)

    def render_context(self) -> List[Dict[str, str]]:
        return [{"role": i.role, "content": i.content} for i in self.items]

# Verification
buffer = EntityPreservingBuffer(token_limit=150)
buffer.add("system", "You are a customer operations agent.")
buffer.add("user", "Hello, I need help with order ORD-9941 for customer CUST-104.")
buffer.add("assistant", "I am looking up that order right now.")
buffer.add("tool", "Order lookup status: delivered to warehouse.")
buffer.add("user", "Can you tell me the weather today in Seattle?")
buffer.add("assistant", "The weather in Seattle is 55F and raining.")

print(f"Total Tokens in Buffer: {buffer.get_total_tokens()} / 150")
print("Retained Messages:")
for msg in buffer.render_context():
    print(f"  [{msg['role']}]: {msg['content'][:60]}...")
