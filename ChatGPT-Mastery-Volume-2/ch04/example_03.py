"""
Production HyDE (Hypothetical Document Embeddings) Engine
Author: Vatsal Shah, Enterprise AI Architect
Transforms questions into declarative hypothetical answers to eliminate query-doc asymmetry.
"""
from typing import List
from openai import AsyncOpenAI
import numpy as np

class HyDERetrievalPipeline:
    def __init__(self, client: AsyncOpenAI, embedding_dim: int = 1024):
        self.client = client
        self.embedding_dim = embedding_dim

    async def generate_hypothetical_document(self, user_question: str) -> str:
        """Generates a speculative, declarative technical answer."""
        system_prompt = (
            "You are an expert technical documentation author. "
            "Write a concise, authoritative excerpt from an enterprise engineering manual "
            "that definitively answers the following question. Do not include conversational remarks; "
            "write pure declarative documentation."
        )
        completion = await self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_question}
            ],
            temperature=0.2,
            max_tokens=250
        )
        return completion.choices[0].message.content

    async def compute_hyde_embedding(self, user_question: str) -> np.ndarray:
        """Generates synthetic doc and returns its Matryoshka-sliced embedding vector."""
        hypo_doc = await self.generate_hypothetical_document(user_question)
        
        # Embed the hypothetical answer instead of the raw question!
        resp = await self.client.embeddings.create(
            model="text-embedding-3-large",
            input=hypo_doc,
            dimensions=self.embedding_dim
        )
        vec = np.array(resp.data[0].embedding, dtype=np.float32)
        norm = np.linalg.norm(vec)
        return vec / norm if norm > 0 else vec
