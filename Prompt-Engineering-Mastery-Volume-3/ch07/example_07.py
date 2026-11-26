"""
Cross-Session Reflexion Memory Store: Persists semantic failure post-mortems
into vector episodic memory to prevent repeating identical errors across future sessions.
"""

from typing import List, Dict, Any
import time


class ReflexionMemoryStore:
    """Records episodic reflection memories across autonomous agent lifecycles."""

    def __init__(self, vector_db_client: Any):
        self.vector_db = vector_db_client

    def record_reflection_event(
        self,
        task_domain: str,
        failed_attempt_summary: str,
        root_cause_critique: str,
        successful_fix_summary: str
    ) -> str:
        """Indexes an episodic reflection entry for future retrieval."""
        memory_payload = {
            "domain": task_domain,
            "failed_approach": failed_attempt_summary,
            "reflection_critique": root_cause_critique,
            "working_solution": successful_fix_summary,
            "timestamp": time.time()
        }

        searchable_text = (
            f"Domain: {task_domain}\n"
            f"Pitfall: {failed_attempt_summary}\n"
            f"Root Cause: {root_cause_critique}\n"
            f"Resolution: {successful_fix_summary}"
        )

        return self.vector_db.insert(
            content=searchable_text,
            metadata=memory_payload
        )
