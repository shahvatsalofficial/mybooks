class MemoryCompactor:
    def __init__(self, summary_threshold_turns: int = 6):
        self.threshold = summary_threshold_turns
        self.uncompacted_turns: List[Dict[str, str]] = []
        self.state_ledger = {
            "primary_goal": "",
            "verified_facts": [],
            "completed_actions": [],
            "pending_milestones": []
        }

    def ingest(self, role: str, content: str):
        self.uncompacted_turns.append({"role": role, "content": content})
        if len(self.uncompacted_turns) >= self.threshold:
            self.compact()

    def compact(self):
        # In production, this prompt is executed against an LLM
        # Here we demonstrate the deterministic state-ledger extraction logic
        facts = []
        actions = []
        for turn in self.uncompacted_turns:
            if "ORD-" in turn["content"]:
                facts.append("Identified active order identifier in conversation.")
            if turn["role"] == "tool":
                actions.append(f"Tool executed: {turn['content'][:40]}...")

        self.state_ledger["verified_facts"].extend(facts)
        self.state_ledger["completed_actions"].extend(actions)
        
        # Clear raw history and retain only the compacted state ledger
        self.uncompacted_turns.clear()

    def render_system_prompt_header(self) -> str:
        return (
            "--- COMPACTED CONVERSATIONAL STATE LEDGER ---\n"
            f"Facts: {json.dumps(self.state_ledger['verified_facts'])}\n"
            f"Actions Taken: {json.dumps(self.state_ledger['completed_actions'])}\n"
            "--------------------------------------------"
        )

# Verification
compactor = MemoryCompactor(summary_threshold_turns=3)
compactor.ingest("user", "Please verify invoice ORD-8812 for enterprise account.")
compactor.ingest("tool", "Database returned invoice total $12,400 with status UNPAID.")
compactor.ingest("assistant", "The invoice ORD-8812 is currently unpaid.")
print("Generated Compacted Header:")
print(compactor.render_system_prompt_header())
