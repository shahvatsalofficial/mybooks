# context_stabilizer.py
from typing import List, Dict

class ContextStabilizer:
    @staticmethod
    def attach_reminder_tail(
        messages: List[Dict[str, str]], 
        constitution_slug: str, 
        current_turn: int, 
        max_turns: int
    ) -> List[Dict[str, str]]:
        remaining_turns = max_turns - current_turn
        
        reminder_content = (
            f"[SYSTEM CONSTITUTIONAL REMINDER - {constitution_slug} | TURN {current_turn}/{max_turns}]\n"
            f"1. Evaluate previous tool observation strictly against Layer 1 Safety Invariants.\n"
            f"2. Negative boundaries remain active: No destructive mutations, no secret exfiltration.\n"
            f"3. Maintain strict XML syntax: <thought>, <action>, <observation>.\n"
            f"4. Budget remaining: {remaining_turns} turns before mandatory termination."
        )
        
        updated_messages = list(messages)
        updated_messages.append({
            "role": "user",
            "content": reminder_content
        })
        return updated_messages
