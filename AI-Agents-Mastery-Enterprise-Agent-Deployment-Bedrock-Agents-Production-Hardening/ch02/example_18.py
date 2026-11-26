import hashlib
import json
from typing import Set, Dict, Any

class IdempotentHopGuard:
    """Guards autonomous agent loops against infinite tool recursion and budget drain."""
    
    def __init__(self, max_hops: int = 5):
        self.max_hops = max_hops
        self.executed_hashes: Set[str] = set()

    def validate_tool_call(self, hop_index: int, tool_name: str, args: Dict[str, Any]) -> bool:
        if hop_index >= self.max_hops:
            raise RuntimeError(f"Circuit tripped: Reached maximum hop ceiling ({self.max_hops}).")
            
        call_signature = f"{tool_name}:{json.dumps(args, sort_keys=True)}"
        call_hash = hashlib.sha256(call_signature.encode()).hexdigest()
        
        if call_hash in self.executed_hashes:
            raise RuntimeError(f"Circuit tripped: Duplicate idempotent tool call detected for {tool_name}.")
            
        self.executed_hashes.add(call_hash)
        return True
