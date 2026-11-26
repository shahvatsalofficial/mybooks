from typing import List, Dict, Any

class ConversationCompactor:
    """Summarizes older conversation turns to maintain bounded token budgets."""

    @staticmethod
    def compact(messages: List[Dict[str, str]], keep_recent: int = 4) -> List[Dict[str, str]]:
        if len(messages) <= keep_recent:
            return messages
        
        older_messages = messages[:-keep_recent]
        recent_messages = messages[-keep_recent:]
        
        summary_bullet_points = []
        for msg in older_messages:
            summary_bullet_points.append(f"{msg['role'].upper()}: {msg['content'][:60]}...")
            
        synthetic_summary = {
            "role": "system",
            "content": "CONVERSATION SUMMARY: Earlier interactions covered: " + " | ".join(summary_bullet_points)
        }
        
        return [synthetic_summary] + recent_messages

if __name__ == "__main__":
    history = [
        {"role": "user", "content": "Check Redis connection status in us-east4."},
        {"role": "model", "content": "Redis node 3 reports 10,000 connected clients."},
        {"role": "user", "content": "What is the memory fragmentation ratio?"},
        {"role": "model", "content": "Fragmentation ratio is currently 1.84."},
        {"role": "user", "content": "Flush volatile keys."},
        {"role": "model", "content": "Flushed 420,000 volatile keys safely."}
    ]
    compacted = ConversationCompactor.compact(history, keep_recent=2)
    print("Compacted history length:", len(compacted))
    print("Summary block:", compacted[0]["content"])
