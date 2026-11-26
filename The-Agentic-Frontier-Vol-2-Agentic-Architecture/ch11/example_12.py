# case_studies/cs10_airgapped_defense_agent.py
"""
Case Study 10: Air-Gapped Intelligence Agent with Local DeepSeek-R1 & Sovereign MCP.
Author: Vatsal Shah — The Agentic Frontier Vol 2
"""

import os
import sys
import logging
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from langgraph.graph import StateGraph, END

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("AirGapped-DefenseAgent")

# ============================================================================
# 1. LOCAL QDRANT VECTOR VAULT & DATA SCHEMAS
# ============================================================================

class IntelligenceReportQuery(BaseModel):
    analyst_query: str
    classification_level: str = "TOP_SECRET"
    retrieved_chunks: List[Dict[str, Any]] = Field(default_factory=list)
    reasoning_chain: Optional[str] = None
    final_briefing: Optional[str] = None
    status: str = "INITIALIZED"

class SovereignLocalQdrantVault:
    def __init__(self, storage_path: str = "./local_qdrant_db"):
        logger.info(" [Sovereign Vault] Initializing Local Qdrant Engine (Zero Cloud Egress)...")
        # Run Qdrant in local disk storage mode (no network ports exposed)
        self.client = QdrantClient(path=storage_path)
        self.collection_name = "classified_intel_docs"
        
        # Ensure local collection exists
        if not self.client.collection_exists(self.collection_name):
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=1024, distance=Distance.COSINE)
            )
            self._seed_local_mock_docs()

    def _seed_local_mock_docs(self):
        """Seeds offline local classified document chunks."""
        mock_docs = [
            (1, [0.01] * 1024, {"doc_id": "SIGINT-2026-881", "text": "Operation Shield Wall logistics depot confirmed at Sector 7G.", "clearance": "TOP_SECRET"}),
            (2, [0.02] * 1024, {"doc_id": "GEOINT-2026-904", "text": "Satellite imagery reveals armor deployment at Grid Ref 449-012.", "clearance": "SECRET"})
        ]
        points = [PointStruct(id=idx, vector=vec, payload=payload) for idx, vec, payload in mock_docs]
        self.client.upsert(collection_name=self.collection_name, points=points)
        logger.info(" [Sovereign Vault] Seeded local classified document vectors.")

    def search_classified_docs(self, query_text: str, limit: int = 3) -> List[Dict[str, Any]]:
        """Searches local Qdrant vector database offline."""
        logger.info(f" [Local Qdrant] Executing offline dense vector search for: '{query_text}'")
        # Simulated dense vector match using local BGE-M3 embedding
        dummy_vector = [0.015] * 1024
        search_res = self.client.search(
            collection_name=self.collection_name,
            query_vector=dummy_vector,
            limit=limit
        )
        results = [hit.payload for hit in search_res]
        return results

# ============================================================================
# 2. LOCAL VLLM DEEPSEEK-R1 SERVING ENGINE MOCK
# ============================================================================

class LocalvLLMDeepSeekR1Engine:
    def __init__(self, model_path: str = "/opt/models/DeepSeek-R1-70B-AWQ"):
        logger.info(f"⚙️ [vLLM Local Engine] Binding DeepSeek-R1 AWQ INT8 on bare-metal A100 GPU...")
        self.model_path = model_path

    def generate_reasoning_and_response(self, prompt: str, context_docs: List[Dict[str, Any]]) -> Dict[str, str]:
        """
        Executes local DeepSeek-R1 chain-of-thought (CoT) reasoning and response generation.
        """
        logger.info(" [DeepSeek-R1 Local] Computing <think> Chain-of-Thought reasoning tokens...")
        
        context_str = "\n".join([f"[{d['doc_id']}] {d['text']}" for d in context_docs])
        
        cot_reasoning = (
            "1. Analyzed query regarding tactical depot locations.\n"
            "2. Cross-referenced SIGINT-2026-881 and GEOINT-2026-904 from local vector store.\n"
            "3. Verified Sector 7G depot matches Grid Ref 449-012 satellite coordinates.\n"
            "4. Confirmed zero external network packet transmission."
        )

        briefing = f"""
===============================================================================
INTELLIGENCE BRIEFING MEMO — TOP SECRET // NOFORN
===============================================================================
TARGET QUERY: {prompt}

[TACTICAL SUMMARY]:
Based on cross-referenced SIGINT and GEOINT reports:
• Logistics depot confirmed at Sector 7G (Ref: SIGINT-2026-881).
• Armor deployment verified at Grid Ref 449-012 (Ref: GEOINT-2026-904).

[PROVENANCE CITATIONS]:
1. Document ID: SIGINT-2026-881 (Classification: TOP_SECRET)
2. Document ID: GEOINT-2026-904 (Classification: SECRET)

[AIR-GAP COMPLIANCE VERIFICATION]:
Executed on Local vLLM Bare-Metal GPU (127.0.0.1). Zero Egress Packets.
===============================================================================
"""
        return {
            "reasoning": cot_reasoning,
            "briefing": briefing.strip()
        }

# ============================================================================
# 3. AGENT GRAPH NODES
# ============================================================================

qdrant_vault = SovereignLocalQdrantVault()
vllm_engine = LocalvLLMDeepSeekR1Engine()

def local_retrieval_node(state: IntelligenceReportQuery) -> Dict[str, Any]:
    """Node 1: Fetches classified doc chunks from local Qdrant DB."""
    logger.info(" [Air-Gapped Agent] Ingesting analyst query...")
    docs = qdrant_vault.search_classified_docs(state.analyst_query)
    return {
        "retrieved_chunks": docs,
        "status": "RETRIEVAL_COMPLETE"
    }

def local_reasoning_node(state: IntelligenceReportQuery) -> Dict[str, Any]:
    """Node 2: Runs local DeepSeek-R1 CoT reasoning via vLLM."""
    logger.info("⚡ [vLLM Node] Invoking local DeepSeek-R1 AWQ INT8 model...")
    res = vllm_engine.generate_reasoning_and_response(state.analyst_query, state.retrieved_chunks)
    return {
        "reasoning_chain": res["reasoning"],
        "final_briefing": res["briefing"],
        "status": "COMPLETED_SUCCESS"
    }

def build_defense_agent_graph():
    builder = StateGraph(IntelligenceReportQuery)
    builder.add_node("local_retrieval", local_retrieval_node)
    builder.add_node("local_reasoning", local_reasoning_node)

    builder.set_entry_point("local_retrieval")
    builder.add_edge("local_retrieval", "local_reasoning")
    builder.add_edge("local_reasoning", END)

    return builder.compile()

if __name__ == "__main__":
    agent = build_defense_agent_graph()

    query = IntelligenceReportQuery(
        analyst_query="Synthesize latest armor deployment and logistics status for Sector 7G."
    )

    output = agent.invoke(query)
    print(f"\nFinal Processing Status: {output['status']}")
    print(output['final_briefing'])
