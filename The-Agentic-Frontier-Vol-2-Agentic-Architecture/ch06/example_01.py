import numpy as np
from typing import List, Dict, Any
from qdrant_client import QdrantClient
from rank_bm25 import BM25Okapi

class ProductionHybridRetriever:
    """
    Enterprise Hybrid Search Engine combining BM25 Lexical and Qdrant Dense Vector Search
    with Reciprocal Rank Fusion (RRF).
    """
    def __init__(self, qdrant_client: QdrantClient, collection_name: str, corpus_texts: List[str], rrf_k: int = 60):
        self.qdrant = qdrant_client
        self.collection = collection_name
        self.rrf_k = rrf_k
        self.corpus = corpus_texts
        
        # Tokenize corpus for BM25
        tokenized_corpus = [doc.lower().split() for doc in corpus_texts]
        self.bm25 = BM25Okapi(tokenized_corpus)

    def retrieve_hybrid(self, query_text: str, query_vector: List[float], top_n: int = 10) -> List[Dict[str, Any]]:
        # 1. Lexical BM25 Search
        tokenized_query = query_text.lower().split()
        bm25_scores = self.bm25.get_scores(tokenized_query)
        bm25_top_indices = np.argsort(bm25_scores)[::-1][:top_n * 2]
        
        bm25_ranks = {self.corpus[idx]: rank + 1 for rank, idx in enumerate(bm25_top_indices)}

        # 2. Dense Vector Search in Qdrant
        vector_results = self.qdrant.search(
            collection_name=self.collection,
            query_vector=query_vector,
            limit=top_n * 2
        )
        vector_ranks = {res.payload["content"]: rank + 1 for rank, res in enumerate(vector_results)}

        # 3. Reciprocal Rank Fusion (RRF)
        all_documents = set(bm25_ranks.keys()).union(set(vector_ranks.keys()))
        rrf_scores = {}

        for doc in all_documents:
            score = 0.0
            if doc in bm25_ranks:
                score += 1.0 / (self.rrf_k + bm25_ranks[doc])
            if doc in vector_ranks:
                score += 1.0 / (self.rrf_k + vector_ranks[doc])
            rrf_scores[doc] = score

        # Sort documents by RRF score descending
        sorted_docs = sorted(rrf_scores.items(), key=lambda item: item[1], reverse=True)
        return [{"content": doc, "rrf_score": score} for doc, score in sorted_docs[:top_n]]
