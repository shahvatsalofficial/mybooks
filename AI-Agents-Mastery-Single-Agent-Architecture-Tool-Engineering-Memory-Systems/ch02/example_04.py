import hashlib
from collections import deque

class CycleBreaker:
    def __init__(self, window_size: int = 5, max_identical_hashes: int = 2):
        self.window_size = window_size
        self.max_identical = max_identical_hashes
        self.action_history: deque = deque(maxlen=window_size)
        self.hash_counts: Dict[str, int] = {}

    def _hash_action(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        canonical_json = json.dumps(arguments, sort_keys=True)
        raw_key = f"{tool_name.lower().strip()}::{canonical_json}"
        return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()

    def record_and_verify(self, tool_name: str, arguments: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        action_hash = self._hash_action(tool_name, arguments)
        
        current_count = self.hash_counts.get(action_hash, 0) + 1
        self.hash_counts[action_hash] = current_count
        
        if len(self.action_history) == self.window_size:
            oldest_hash = self.action_history[0]
            self.hash_counts[oldest_hash] = max(0, self.hash_counts[oldest_hash] - 1)

        self.action_history.append(action_hash)

        if current_count > self.max_identical:
            return False, f"CIRCUIT BREAKER: Duplicate action detected {current_count} times for {tool_name}. Interrupting loop."

        return True, None

# Verification
breaker = CycleBreaker(window_size=4, max_identical_hashes=2)
actions = [
    ("fetch_user", {"id": "104"}),
    ("fetch_orders", {"user_id": "104"}),
    ("fetch_user", {"id": "104"}),
    ("fetch_user", {"id": "104"})  # Third attempt triggers circuit breaker
]

for tool, args in actions:
    allowed, reason = breaker.record_and_verify(tool, args)
    print(f"Action: {tool}({args}) -> Allowed: {allowed} | Warning: {reason}")
