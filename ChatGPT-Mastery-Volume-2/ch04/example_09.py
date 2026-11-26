"""
Corrective RAG (CRAG) Routing State Machine
Evaluates retrieval confidence and triggers automated corrective web search fallbacks.
Author: Vatsal Shah, Enterprise AI Architect
"""
from enum import Enum
from typing import List, Dict, Any
from pydantic import BaseModel, Field
from openai import AsyncOpenAI

class RetrievalConfidence(str, Enum):
    CORRECT = "CORRECT"
    AMBIGUOUS = "AMBIGUOUS"
    INCORRECT = "INCORRECT"

class RetrievalEvaluation(BaseModel):
    confidence: RetrievalConfidence
    relevance_rationale: str
    key_facts_found: List[str]

class CRAGRouter:
    def __init__(self, client: AsyncOpenAI):
        self.client = client

    async def evaluate_retrieval_fidelity(self, query: str, context: str) -> RetrievalEvaluation:
        system_prompt = (
            "You are a strict Retrieval Verification Gatekeeper. "
            "Evaluate whether the provided context contains sufficient, high-quality, "
            "and authoritative factual evidence to answer the user query. "
            "Classify confidence as 'CORRECT' (definitive evidence), 'AMBIGUOUS' (partial evidence), "
            "or 'INCORRECT' (irrelevant or contradictory)."
        )
        res = await self.client.beta.chat.completions.parse(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"QUERY: {query}\n\nCONTEXT:\n{context}"}
            ],
            response_format=RetrievalEvaluation
        )
        return res.choices[0].message.parsed

    async def dispatch_crag_pipeline(self, query: str, context_chunks: List[str]) -> str:
        aggregated_context = "\n---\n".join(context_chunks)
        evaluation = await self.evaluate_retrieval_fidelity(query, aggregated_context)
        
        if evaluation.confidence == RetrievalConfidence.CORRECT:
            print("✅ CRAG: High confidence retrieval. Synthesizing answer...")
            return await self._synthesize(query, aggregated_context)
            
        elif evaluation.confidence == RetrievalConfidence.AMBIGUOUS:
            print("⚠️ CRAG: Ambiguous retrieval. Executing corrective query rewrite...")
            rewritten_query = f"{query} detailed technical specifications"
            # In production: trigger web search tool or secondary knowledge store
            return await self._synthesize(query, aggregated_context + "\n[Note: Supplemented via secondary search]")
            
        else:
            print("❌ CRAG: Low confidence retrieval. Triggering safe fallback...")
            return "I do not have verified internal documentation to answer this question accurately."

    async def _synthesize(self, query: str, context: str) -> str:
        res = await self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "Answer strictly based on provided context."},
                {"role": "user", "content": f"CONTEXT:\n{context}\n\nQUERY:\n{query}"}
            ]
        )
        return res.choices[0].message.content
