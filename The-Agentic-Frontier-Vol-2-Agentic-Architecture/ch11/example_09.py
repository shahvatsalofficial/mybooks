# case_studies/cs06_legal_graphrag_agent.py
"""
Case Study 06: Legal Research Agent with Microsoft GraphRAG Traversal.
Author: Vatsal Shah — The Agentic Frontier Vol 2
"""

import os
import time
import logging
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
import networkx as nx
from langgraph.graph import StateGraph, END

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("LegalGraphRAGAgent")

# ============================================================================
# 1. LEGAL GRAPH SCHEMAS & ENTITY MODELS
# ============================================================================

class LegalCaseEntity(BaseModel):
    case_id: str
    case_name: str
    citation: str
    year: int
    is_good_law: bool = True
    overruled_by: Optional[str] = None

class PrecedentChainHop(BaseModel):
    source_case: str
    relationship: str  # CITES, OVERRULES, DISTINGUISHES, APPLIES
    target_case: str
    hop_level: int

class LegalResearchState(BaseModel):
    legal_query: str
    seed_cases: List[str] = Field(default_factory=list)
    traversed_chain: List[PrecedentChainHop] = Field(default_factory=list)
    overruled_warnings: List[str] = Field(default_factory=list)
    final_memo: Optional[str] = None
    status: str = "INITIALIZED"

# ============================================================================
# 2. NEIGHBORHOOD GRAPH TRAVERSAL ENGINE
# ============================================================================

class LegalKnowledgeGraphManager:
    def __init__(self):
        # Build local NetworkX graph representing 4-hop legal precedent network
        self.graph = nx.DiGraph()
        self._populate_mock_legal_graph()

    def _populate_mock_legal_graph(self):
        # Nodes: Legal Cases
        self.graph.add_node("CASE_A", name="Smith v. TechCorp (2018)", good_law=True)
        self.graph.add_node("CASE_B", name="Jones v. DataInc (2014)", good_law=False, overruled_by="CASE_C")
        self.graph.add_node("CASE_C", name="Apex Holdings v. State (2021)", good_law=True)
        self.graph.add_node("STATUTE_D", name="Digital Privacy Act Sec 402 (2023)", good_law=True)

        # Edges: Citation & Overruling Relationships
        self.graph.add_edge("CASE_A", "CASE_B", rel="CITES")
        self.graph.add_edge("CASE_C", "CASE_B", rel="OVERRULES")
        self.graph.add_edge("STATUTE_D", "CASE_C", rel="AMENDS")

    def traverse_precedent_chain(self, seed_case: str, max_hops: int = 4) -> List[PrecedentChainHop]:
        """Traverses multi-hop citation graph up to max_hops level."""
        logger.info(f"️ [GraphRAG] Executing {max_hops}-hop precedent traversal from seed {seed_case}...")
        hops = []
        visited = set()
        queue = [(seed_case, 1)]

        while queue:
            curr_node, current_hop = queue.pop(0)
            if current_hop > max_hops or curr_node in visited:
                continue
            visited.add(curr_node)

            # Traversal outgoing and incoming edges
            for neighbor in self.graph.successors(curr_node):
                rel = self.graph[curr_node][neighbor].get("rel", "RELATED_TO")
                hops.append(PrecedentChainHop(
                    source_case=curr_node,
                    relationship=rel,
                    target_case=neighbor,
                    hop_level=current_hop
                ))
                queue.append((neighbor, current_hop + 1))

            for predecessor in self.graph.predecessors(curr_node):
                rel = self.graph[predecessor][curr_node].get("rel", "RELATED_TO")
                hops.append(PrecedentChainHop(
                    source_case=predecessor,
                    relationship=rel,
                    target_case=curr_node,
                    hop_level=current_hop
                ))
                queue.append((predecessor, current_hop + 1))

        return hops

# ============================================================================
# 3. AGENT GRAPH NODES
# ============================================================================

def seed_search_node(state: LegalResearchState) -> Dict[str, Any]:
    """
    Search Node: Performs vector search to identify initial seed precedent cases.
    """
    logger.info(f" [Legal Agent] Performing initial vector lookup for query: {state.legal_query}")
    # Simulated vector search returns initial seed case
    seed_cases = ["CASE_A"]
    return {"seed_cases": seed_cases, "status": "SEEDS_FOUND"}

def graph_traversal_node(state: LegalResearchState) -> Dict[str, Any]:
    """
    Graph Traversal Node: Executes GraphRAG 4-hop chain traversal over Neo4j/NetworkX.
    """
    kg_mgr = LegalKnowledgeGraphManager()
    all_hops = []
    warnings = []

    for seed in state.seed_cases:
        hops = kg_mgr.traverse_precedent_chain(seed, max_hops=4)
        all_hops.extend(hops)
        
        # Check for overruled cases in traversal path
        for hop in hops:
            if hop.relationship == "OVERRULES":
                warn = f"⚠️ CRITICAL PRECEDENT WARNING: {hop.target_case} was OVERRULED by {hop.source_case}!"
                warnings.append(warn)
                logger.warning(warn)

    return {
        "traversed_chain": all_hops,
        "overruled_warnings": warnings,
        "status": "TRAVERSAL_COMPLETE"
    }

def memo_generation_node(state: LegalResearchState) -> Dict[str, Any]:
    """
    Synthesis Node: Generates verified legal research memorandum.
    """
    logger.info(" [Legal Agent] Synthesizing Verified Precedent Briefing Memo...")
    query = state.legal_query
    chain = state.traversed_chain
    warnings = state.overruled_warnings

    chain_formatted = "\n".join([f"  [Hop {h.hop_level}] {h.source_case} --({h.relationship})--> {h.target_case}" for h in chain])
    warnings_formatted = "\n".join(warnings) if warnings else "  None. All cited precedents are good law."

    memo = f"""
===============================================================================
LEGAL RESEARCH MEMORANDUM — PRIVILEGED & CONFIDENTIAL
Query: {query}
===============================================================================

[VERIFIED 4-HOP PRECEDENT CITATION GRAPH]:
{chain_formatted}

[GOOD LAW AUDIT & OVERRULED WARNINGS]:
{warnings_formatted}

[RECOMMENDED TRIAL STRATEGY]:
Based on 4-hop GraphRAG analysis, do NOT rely directly on Case B as primary authority,
as it was explicitly OVERRULED by Case C (Apex Holdings v. State). Frame argument around
Case C as modified by Digital Privacy Act Sec 402.

===============================================================================
"""
    return {
        "final_memo": memo.strip(),
        "status": "RESEARCH_COMPLETE"
    }

# ============================================================================
# 4. GRAPH COMPILATION & TEST EXECUTION
# ============================================================================

def build_legal_agent_graph():
    builder = StateGraph(LegalResearchState)
    builder.add_node("seed_search", seed_search_node)
    builder.add_node("graph_traversal", graph_traversal_node)
    builder.add_node("memo_generation", memo_generation_node)

    builder.set_entry_point("seed_search")
    builder.add_edge("seed_search", "graph_traversal")
    builder.add_edge("graph_traversal", "memo_generation")
    builder.add_edge("memo_generation", END)

    return builder.compile()

if __name__ == "__main__":
    legal_graph = build_legal_agent_graph()
    
    init_state = LegalResearchState(
        legal_query="Can trade secret claims proceed if data was shared under non-binding MOU?"
    )
    
    res = legal_graph.invoke(init_state)
    print(f"\nFinal Status: {res['status']}")
    print(res['final_memo'])
