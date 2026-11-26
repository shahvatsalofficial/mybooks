"""
Hands-On Lab: Automated RAG Triad Guardrail Auditor
Evaluates Context Relevance, Groundedness, and Answer Relevance using programmatic LLM judges.
Author: Vatsal Shah, Enterprise AI Architect
"""
import os
import json
import asyncio
from openai import AsyncOpenAI
from pydantic import BaseModel, Field

client = AsyncOpenAI()

class ContextRelevanceScore(BaseModel):
    relevance_score: float = Field(ge=0.0, le=1.0, description="Score 0.0 to 1.0 on how directly context answers query")
    reasoning: str = Field(description="Audit justification")

class GroundednessScore(BaseModel):
    groundedness_score: float = Field(ge=0.0, le=1.0, description="Score 0.0 to 1.0 on factual support from context")
    unsupported_claims: list[str] = Field(description="List of hallucinated or unverified claims found in answer")

async def evaluate_context_relevance(user_query: str, retrieved_context: str) -> ContextRelevanceScore:
    prompt = f"USER QUERY: {user_query}

RETRIEVED CONTEXT:
{retrieved_context}"
    res = await client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a rigid Information Retrieval Auditor. Evaluate Context Relevance."},
            {"role": "user", "content": prompt}
        ],
        response_format=ContextRelevanceScore
    )
    return res.choices[0].message.parsed

async def evaluate_groundedness(retrieved_context: str, generated_answer: str) -> GroundednessScore:
    prompt = f"SOURCE CONTEXT:
{retrieved_context}

GENERATED ANSWER:
{generated_answer}"
    res = await client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a Factual Verification Auditor. Verify Groundedness."},
            {"role": "user", "content": prompt}
        ],
        response_format=GroundednessScore
    )
    return res.choices[0].message.parsed

async def run_audit_demo():
    print("
=======================================================")
    print("🎯 RUNNING AUTOMATED RAG TRIAD EVALUATION AUDIT")
    print("=======================================================
")

    query = "What is the mandatory encryption standard for client data at rest?"
    good_context = (
        "Enterprise Security Policy Section 4.1: All client transactional and personal "
        "data at rest must be encrypted using AES-256 with customer-managed keys rotated annually."
    )
    hallucinated_answer = (
        "Client data at rest is encrypted using AES-256 with annually rotated keys. "
        "Additionally, all backups are mirrored to offsite physical vaults in Switzerland daily."
    )

    print(f"Query: {query}")
    print(f"Context: {good_context}")
    print(f"Answer: {hallucinated_answer}
")

    print("Auditing Context Relevance...")
    c_eval = await evaluate_context_relevance(query, good_context)
    print(f"   Context Relevance Score: {c_eval.relevance_score * 100:.1f}% ({c_eval.reasoning})")

    print("
Auditing Groundedness (Hallucination Detection)...")
    g_eval = await evaluate_groundedness(good_context, hallucinated_answer)
    print(f"   Groundedness Score: {g_eval.groundedness_score * 100:.1f}%")
    if g_eval.unsupported_claims:
        print("   ⚠️ Detected Hallucinated Claims:")
        for claim in g_eval.unsupported_claims:
            print(f"     • {claim}")

    print("
✅ RAG Triad Audit Completed!")

if __name__ == "__main__":
    asyncio.run(run_audit_demo())
