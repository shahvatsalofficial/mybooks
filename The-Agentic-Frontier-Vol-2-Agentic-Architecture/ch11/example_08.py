# case_studies/cs05_executive_mem0_agent.py
"""
Case Study 05: Executive Support Agent with Mem0 12-Month Memory.
Author: Vatsal Shah — The Agentic Frontier Vol 2
"""

import os
import time
import logging
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from mem0 import Memory
from langgraph.graph import StateGraph, END

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("ExecutiveMem0Agent")

# ============================================================================
# 1. MEMORY & EXECUTIVE CONTEXT SCHEMAS
# ============================================================================

class ExecutivePreference(BaseModel):
    user_id: str = "CEO_EXEC_01"
    category: str  # e.g., "MEETING_PREFERENCE", "TRAVEL", "MA_STRATEGY"
    preference_key: str
    preference_value: str
    confidence: float = 0.95
    updated_at_epoch: int = Field(default_factory=lambda: int(time.time()))

class ExecutiveTaskState(BaseModel):
    user_id: str = "CEO_EXEC_01"
    raw_query: str
    retrieved_memories: List[Dict[str, Any]] = Field(default_factory=list)
    reconciled_context: Optional[str] = None
    final_brief: Optional[str] = None
    status: str = "INITIALIZED"

# ============================================================================
# 2. MEM0 MEMORY GRAPH MANAGER
# ============================================================================

class ExecutiveMemoryManager:
    def __init__(self):
        # Configure Mem0 with Qdrant vector store and custom memory config
        config = {
            "vector_store": {
                "provider": "qdrant",
                "config": {
                    "host": os.getenv("QDRANT_HOST", "localhost"),
                    "port": 6333,
                    "collection_name": "executive_memories"
                }
            },
            "version": "v1.1"
        }
        # Fallback simulation if Qdrant instance is offline for demo safety
        try:
            self.memory = Memory.from_config(config)
            self.is_live = True
        except Exception:
            logger.warning("⚠️ Qdrant host offline. Initializing in-memory mock Mem0 runner.")
            self.is_live = False
            self.mock_store: List[Dict[str, Any]] = [
                {
                    "id": "mem-101",
                    "text": "CEO prefers maximum 30-minute meetings and no Friday afternoon internal calls.",
                    "created_at": "2026-01-15T10:00:00Z",
                    "metadata": {"category": "MEETING_PREFERENCE"}
                },
                {
                    "id": "mem-102",
                    "text": "Target valuation for Acme Corp acquisition is capped at $45M (Updated July 2026).",
                    "created_at": "2026-07-20T14:30:00Z",
                    "metadata": {"category": "MA_STRATEGY"}
                }
            ]

    def add_interaction_memory(self, user_id: str, interaction_text: str, metadata: Dict[str, Any]):
        """Extracts facts and updates Mem0 memory graph."""
        logger.info(f" [Mem0] Processing interaction memory for user {user_id}...")
        if self.is_live:
            self.memory.add(interaction_text, user_id=user_id, metadata=metadata)
        else:
            self.mock_store.append({
                "id": f"mem-{time.time_ns()}",
                "text": interaction_text,
                "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "metadata": metadata
            })
            logger.info(" [Mem0 Mock] Added memory entry.")

    def search_memories(self, user_id: str, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Retrieves and reconciles historical context relevant to query."""
        logger.info(f" [Mem0] Searching 12-month memory graph for query: '{query}'...")
        if self.is_live:
            results = self.memory.search(query, user_id=user_id, limit=limit)
            return results.get("results", [])
        else:
            # Mock semantic search filtering
            query_terms = query.lower().split()
            matched = []
            for item in self.mock_store:
                if any(t in item["text"].lower() for t in query_terms):
                    matched.append(item)
            return matched if matched else self.mock_store[:limit]

# ============================================================================
# 3. AGENT GRAPH NODES
# ============================================================================

def memory_retrieval_node(state: ExecutiveTaskState) -> Dict[str, Any]:
    """
    Retrieval Node: Fetches historical preferences and episodic events from Mem0.
    """
    logger.info(f" [Executive Agent] Ingesting query: {state.raw_query}")
    mem_mgr = ExecutiveMemoryManager()
    memories = mem_mgr.search_memories(state.user_id, state.raw_query)
    
    return {
        "retrieved_memories": memories,
        "status": "MEMORIES_RETRIEVED"
    }

def conflict_resolution_node(state: ExecutiveTaskState) -> Dict[str, Any]:
    """
    Conflict Resolution Node: Reconciles outdated vs updated preference contradictions.
    """
    logger.info("⚖️ [Conflict Resolution] Reconciling memory timestamps & preference overrides...")
    memories = state.retrieved_memories
    
    if not memories:
        reconciled = "No specific historical preferences found. Operating under default executive guidelines."
    else:
        # Sort by creation date to prioritize recent updates
        sorted_memories = sorted(memories, key=lambda x: x.get("created_at", ""), reverse=True)
        reconciled_facts = [f"• {m['text']} (Logged: {m.get('created_at', 'N/A')})" for m in sorted_memories]
        reconciled = "\n".join(reconciled_facts)

    logger.info(f" Reconciled Context:\n{reconciled}")
    return {
        "reconciled_context": reconciled,
        "status": "CONTEXT_RECONCILED"
    }

def brief_generation_node(state: ExecutiveTaskState) -> Dict[str, Any]:
    """
    Brief Generator: Synthesizes executive briefing memo incorporating reconciled context.
    """
    logger.info(" [Executive Agent] Synthesizing Executive Briefing Memo...")
    query = state.raw_query
    context = state.reconciled_context

    brief = f"""
===============================================================================
EXECUTIVE BRIEFING MEMO — CONFIDENTIAL
Target Query: {query}
===============================================================================

[RECONCILED HISTORICAL CONTEXT (Mem0 12-Month Recall)]:
{context}

[EXECUTIVE ACTION RECOMMENDATION]:
Based on your updated preferences logged above, the recommended strategy is:
1. Schedule a max 30-minute prep call with the M&A advisory team.
2. Maintain strict $45M valuation ceiling during upcoming Acme Corp negotiations.
3. Ensure no Friday afternoon internal review calls are placed on calendar.

===============================================================================
"""
    return {
        "final_brief": brief.strip(),
        "status": "BRIEF_COMPLETE"
    }

# ============================================================================
# 4. GRAPH COMPILATION & TEST EXECUTION
# ============================================================================

def build_executive_agent_graph():
    builder = StateGraph(ExecutiveTaskState)
    builder.add_node("memory_retrieval", memory_retrieval_node)
    builder.add_node("conflict_resolution", conflict_resolution_node)
    builder.add_node("brief_generation", brief_generation_node)

    builder.set_entry_point("memory_retrieval")
    builder.add_edge("memory_retrieval", "conflict_resolution")
    builder.add_edge("conflict_resolution", "brief_generation")
    builder.add_edge("brief_generation", END)

    return builder.compile()

if __name__ == "__main__":
    agent_graph = build_executive_agent_graph()
    
    test_query = ExecutiveTaskState(
        raw_query="Prepare meeting brief for Acme Corp acquisition and check my calendar rules for Friday."
    )
    
    final_output = agent_graph.invoke(test_query)
    print(f"\nFinal Status: {final_output['status']}")
    print(final_output['final_brief'])
