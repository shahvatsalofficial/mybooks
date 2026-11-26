class TokenBudgetViolationError(Exception):
    pass

class TokenBudgetGovernor:
    def __init__(
        self,
        max_context_limit: int = 16000,
        generation_headroom: int = 3000,
        system_reserve: int = 2000
    ):
        self.max_context = max_context_limit
        self.generation_headroom = generation_headroom
        self.system_reserve = system_reserve
        self.max_dynamic_payload = max_context_limit - generation_headroom - system_reserve

    def allocate_and_prune(
        self,
        system_prompt: str,
        rag_passages: List[Dict[str, Any]],
        conversation_turns: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """Prunes dynamic RAG and dialogue to guarantee strict compliance with token ceiling."""
        def estimate(t: str) -> int:
            return len(t) // 4 + 1

        sys_tokens = estimate(system_prompt)
        if sys_tokens > self.system_reserve:
            raise TokenBudgetViolationError(f"System prompt ({sys_tokens} tokens) exceeds allocation ({self.system_reserve}).")

        # Budget remaining for RAG + Dialogue
        available_dynamic = self.max_dynamic_payload

        # Priority 1: Dialogue (Last 4 turns preserved)
        dialogue_tokens = sum(estimate(t["content"]) for t in conversation_turns[-4:])
        pruned_turns = conversation_turns[-4:]

        # Remaining capacity for RAG
        rag_budget = available_dynamic - dialogue_tokens
        accepted_passages = []
        current_rag_tokens = 0

        # Sort RAG passages by relevance score descending
        sorted_passages = sorted(rag_passages, key=lambda x: x.get("score", 0.0), reverse=True)

        for p in sorted_passages:
            p_tokens = estimate(p["text"])
            if current_rag_tokens + p_tokens <= rag_budget:
                accepted_passages.append(p)
                current_rag_tokens += p_tokens
            else:
                break  # Shed remaining passages

        total_input_tokens = sys_tokens + dialogue_tokens + current_rag_tokens

        return {
            "total_estimated_input_tokens": total_input_tokens,
            "allocated_generation_headroom": self.generation_headroom,
            "retained_rag_passages_count": len(accepted_passages),
            "pruned_dialogue_turns_count": len(pruned_turns),
            "payload_ready": True
        }
