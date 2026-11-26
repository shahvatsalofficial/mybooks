# enterprise_rag_pipeline.py — High-Precision Two-Stage Hybrid Retrieval
import math
import re
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass
import numpy as np

@dataclass
class DocumentChunk:
    chunk_id: str
    parent_id: str
    content: str
    metadata: Dict[str, Any]
    dense_vector: List[float] = None

class LuceneBM25Index:
    """In-memory Lucene BM25 engine with term saturation and length normalization."""
    def __init__(self, k1: float = 1.2, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.corpus: List[DocumentChunk] = []
        self.doc_lengths: List[int] = []
        self.avg_doc_len: float = 0.0
        self.inverted_index: Dict[str, List[Tuple[int, int]]] = {} # term -> [(doc_idx, freq)]
        self.doc_count: int = 0

    def _tokenize(self, text: str) -> List[str]:
        return re.findall(r'\b\w+\b', text.lower())

    def fit(self, chunks: List[DocumentChunk]):
        self.corpus = chunks
        self.doc_count = len(chunks)
        self.doc_lengths = [len(self._tokenize(c.content)) for c in chunks]
        self.avg_doc_len = sum(self.doc_lengths) / max(1, self.doc_count)

        for doc_idx, chunk in enumerate(chunks):
            tokens = self._tokenize(chunk.content)
            counts = {}
            for t in tokens:
                counts[t] = counts.get(t, 0) + 1
            for t, freq in counts.items():
                if t not in self.inverted_index:
                    self.inverted_index[t] = []
                self.inverted_index[t].append((doc_idx, freq))

    def search(self, query: str, top_k: int = 50) -> List[Tuple[DocumentChunk, float]]:
        query_tokens = self._tokenize(query)
        scores = np.zeros(self.doc_count)

        for term in query_tokens:
            if term not in self.inverted_index:
                continue
            postings = self.inverted_index[term]
            df = len(postings)
            idf = math.log(1.0 + (self.doc_count - df + 0.5) / (df + 0.5))

            for doc_idx, freq in postings:
                dl = self.doc_lengths[doc_idx]
                numerator = freq * (self.k1 + 1.0)
                denominator = freq + self.k1 * (1.0 - self.b + self.b * (dl / self.avg_doc_len))
                scores[doc_idx] += idf * (numerator / denominator)

        ranked_indices = np.argsort(scores)[::-1][:top_k]
        return [(self.corpus[i], float(scores[i])) for i in ranked_indices if scores[i] > 0]

class DenseCosineIndex:
    """Exact cosine vector index representing Azure AI Search HNSW backend."""
    def __init__(self):
        self.chunks: List[DocumentChunk] = []
        self.vectors: np.ndarray = None

    def fit(self, chunks: List[DocumentChunk]):
        self.chunks = chunks
        vector_matrix = [c.dense_vector for c in chunks]
        self.vectors = np.array(vector_matrix, dtype=np.float32)
        # Normalize for cosine dot-product
        norms = np.linalg.norm(self.vectors, axis=1, keepdims=True)
        self.vectors = self.vectors / np.maximum(norms, 1e-9)

    def search(self, query_vector: List[float], top_k: int = 50) -> List[Tuple[DocumentChunk, float]]:
        q_vec = np.array(query_vector, dtype=np.float32)
        q_norm = np.linalg.norm(q_vec)
        if q_norm > 0:
            q_vec = q_vec / q_norm
        similarities = np.dot(self.vectors, q_vec)
        ranked_indices = np.argsort(similarities)[::-1][:top_k]
        return [(self.chunks[i], float(similarities[i])) for i in ranked_indices]

class ReciprocalRankFusionEngine:
    """Normalizes and fuses disparate dense and sparse ranking lists."""
    @staticmethod
    def fuse(
        dense_results: List[Tuple[DocumentChunk, float]],
        sparse_results: List[Tuple[DocumentChunk, float]],
        k: int = 60,
        top_k: int = 30
    ) -> List[Tuple[DocumentChunk, float]]:
        rrf_scores: Dict[str, float] = {}
        chunk_map: Dict[str, DocumentChunk] = {}

        # Process Dense List
        for rank, (chunk, _) in enumerate(dense_results):
            cid = chunk.chunk_id
            chunk_map[cid] = chunk
            rrf_scores[cid] = rrf_scores.get(cid, 0.0) + (1.0 / (k + (rank + 1)))

        # Process Sparse BM25 List
        for rank, (chunk, _) in enumerate(sparse_results):
            cid = chunk.chunk_id
            chunk_map[cid] = chunk
            rrf_scores[cid] = rrf_scores.get(cid, 0.0) + (1.0 / (k + (rank + 1)))

        sorted_items = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
        return [(chunk_map[cid], score) for cid, score in sorted_items]

class CrossEncoderReRanker:
    """Mock cross-encoder representing BGE-Reranker-Large joint attention."""
    def __init__(self, model_name: str = "BAAI/bge-reranker-large"):
        self.model_name = model_name

    def rerank(self, query: str, candidates: List[DocumentChunk], top_k: int = 5) -> List[Tuple[DocumentChunk, float]]:
        scored: List[Tuple[DocumentChunk, float]] = []
        q_words = set(query.lower().split())

        for c in candidates:
            # Cross-encoder joint attention simulation: word overlap + length cohesion
            c_words = set(c.content.lower().split())
            overlap = len(q_words.intersection(c_words))
            # Semantic cross-scoring function
            score = 1.0 / (1.0 + math.exp(-0.8 * (overlap - 2)))
            scored.append((c, score))

        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_k]
