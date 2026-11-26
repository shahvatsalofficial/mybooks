"""
Asynchronous Memory Consolidation Engine: Synthesizes completed multi-turn
ReAct trajectories into durable, deduplicated semantic facts during agent idle cycles.
"""

from typing import List, Dict, Any
import json


class MemoryConsolidationWorker:
    """Extracts distilled semantic knowledge from historical execution traces."""

    def __init__(self, semantic_store: Any, llm_client: Any):
        self.semantic_store = semantic_store
        self.llm_client = llm_client

    def consolidate_session_trace(self, session_id: str, raw_trace: List[Dict[str, Any]]) -> int:
        """
        Processes completed session turns, extracts durable facts, and persists them.
        Returns count of newly indexed semantic records.
        """
        formatted_trace = json.dumps(raw_trace, indent=2)

        prompt = f"""
You are an Enterprise Knowledge Extraction Engine. Analyze this completed agent trace:
<execution_trace>
{formatted_trace}
</execution_trace>

Extract any permanent architectural facts, corrected tool configurations, or operational
learnings that should be remembered for future sessions.
Output MUST be a JSON array of objects:
[
  {{"fact": "...", "importance": 0.85, "category": "INFRASTRUCTURE"}}
]
Do not include transient status messages. If no permanent facts are discovered, return [].
"""
        response = self.llm_client.generate(prompt)
        try:
            facts = json.loads(response)
        except json.JSONDecodeError:
            return 0

        persisted_count = 0
        for item in facts:
            fact_text = item.get("fact", "").strip()
            importance = float(item.get("importance", 0.5))
            category = item.get("category", "GENERAL")

            if fact_text:
                self.semantic_store.index_fact(
                    content=fact_text,
                    importance=importance,
                    metadata={"source_session": session_id, "category": category}
                )
                persisted_count += 1

        return persisted_count
