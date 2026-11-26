"""
Enterprise Hybrid RAG Engine with Matryoshka Slicing & RRF
Author: Vatsal Shah, Enterprise AI Architect
Version: 2.0 (Production Hardened)
"""
import os
import math
import asyncio
import numpy as np
from typing import List, Dict, Any, Tuple
from rank_bm25 import BM25Okapi
from openai import AsyncOpenAI

class DocumentChunk:
    def __init__(self, chunk_id: str, content: str, metadata: Dict[str, Any] = None):
        self.chunk_id = chunk_id
        self.content = content
        self.metadata = metadata or {}
        self.embedding: np.ndarray = None

class EnterpriseHybridRAGEngine:
    def __init__(self, api_key: str = None, embedding_dim: int = 1024, rrf_k: int = 60):
        self.client = AsyncOpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))
        self.embedding_dim = embedding_dim
        self.rrf_k = rrf_k
        self.corpus: List[DocumentChunk] = []
        self.bm25: BM25Okapi = None
        self.vector_index: np.ndarray = None

    async def _compute_embeddings_batch(self, texts: List[str]) -> List[np.ndarray]:
        """Fetches Matryoshka-sliced embeddings from OpenAI API."""
        response = await self.client.embeddings.create(
            model="text-embedding-3-large",
            input=texts,
            dimensions=self.embedding_dim
        )
        embeddings = []
        for item in response.data:
            vec = np.array(item.embedding, dtype=np.float32)
            # Re-normalize to guarantee unit length
            norm = np.linalg.norm(vec)
            if norm > 0:
                vec = vec / norm
            embeddings.append(vec)
        return embeddings

    async def index_documents(self, documents: List[Dict[str, str]]) -> None:
        """Indexes a corpus of raw documents into BM25 and Matryoshka Vector spaces."""
        print(f"Indexing {len(documents)} enterprise documents...")
        self.corpus = [
            DocumentChunk(chunk_id=doc["id"], content=doc["text"], metadata=doc.get("metadata"))
            for doc in documents
        ]

        # 1. Build Sparse BM25 Index
        tokenized_corpus = [doc.content.lower().split() for doc in self.corpus]
        self.bm25 = BM25Okapi(tokenized_corpus)

        # 2. Build Dense Matryoshka Vector Index
        batch_size = 64
        all_embeddings = []
        for i in range(0, len(self.corpus), batch_size):
            batch_texts = [doc.content for doc in self.corpus[i:i + batch_size]]
            batch_embeddings = await self._compute_embeddings_batch(batch_texts)
            all_embeddings.extend(batch_embeddings)

        for doc, emb in zip(self.corpus, all_embeddings):
            doc.embedding = emb

        self.vector_index = np.vstack(all_embeddings)
        print("✅ Hybrid indexing completed successfully!")

    async def search(self, query: str, top_k: int = 5) -> List[Tuple[DocumentChunk, float]]:
        """Executes parallel Dense + BM25 search and merges via Reciprocal Rank Fusion."""
        # Step 1: Run BM25 Sparse Retrieval
        tokenized_query = query.lower().split()
        bm25_scores = self.bm25.get_scores(tokenized_query)
        # Sort descending by score
        bm25_ranked_indices = np.argsort(bm25_scores)[::-1]

        # Step 2: Run Dense Matryoshka Vector Retrieval
        query_embedding_list = await self._compute_embeddings_batch([query])
        query_vec = query_embedding_list[0]
        
        # Dot product cosine similarity across normalized matrix
        dense_scores = np.dot(self.vector_index, query_vec)
        dense_ranked_indices = np.argsort(dense_scores)[::-1]

        # Step 3: Compute Reciprocal Rank Fusion (RRF) Scores
        rrf_scores: Dict[int, float] = {}

        # Aggregate BM25 ranks
        for rank, doc_idx in enumerate(bm25_ranked_indices[:50]):
            rrf_scores[doc_idx] = rrf_scores.get(doc_idx, 0.0) + (1.0 / (self.rrf_k + (rank + 1)))

        # Aggregate Dense ranks
        for rank, doc_idx in enumerate(dense_ranked_indices[:50]):
            rrf_scores[doc_idx] = rrf_scores.get(doc_idx, 0.0) + (1.0 / (self.rrf_k + (rank + 1)))

        # Step 4: Sort by combined RRF score descending
        sorted_candidates = sorted(rrf_scores.items(), key=lambda item: item[1], reverse=True)
        
        results = [
            (self.corpus[doc_idx], score)
            for doc_idx, score in sorted_candidates[:top_k]
        ]
        return results

    async def generate_grounded_answer(self, user_query: str) -> str:
        """Retrieves top chunks and synthesizes an authoritative grounded response."""
        retrieved_results = await self.search(user_query, top_k=3)
        
        context_blocks = []
        for i, (doc, rrf_score) in enumerate(retrieved_results):
            context_blocks.append(
                f"[Source {i+1} - ID: {doc.chunk_id} (RRF: {rrf_score:.4f})]:
{doc.content}"
            )
        formatted_context = "

".join(context_blocks)

        system_instruction = (
            "You are an authoritative Enterprise Knowledge Officer. "
            "Answer the user query strictly utilizing the factual context provided below. "
            "If the context does not contain sufficient facts to answer definitively, state "
            "'I do not have sufficient internal documentation to verify this claim.' "
            "Always cite sources using [Source X]."
        )

        user_payload = f"FACTUAL CONTEXT:
{formatted_context}

USER QUERY:
{user_query}"

        completion = await self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": user_payload}
            ],
            temperature=0.0
        )
        return completion.choices[0].message.content
