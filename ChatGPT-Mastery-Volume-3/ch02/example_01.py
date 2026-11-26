"""
enterprise_rag_engine.py
Production-grade Hybrid RAG Engine with Hierarchical Parent-Child Indexing and RRF.
"""
import math
import uuid
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass, field
import numpy as np

@dataclass
class ChildChunk:
    chunk_id: str
    parent_id: str
    content: str
    tokens: int
    vector: np.ndarray = field(default_factory=lambda: np.zeros(0))

@dataclass
class ParentChunk:
    parent_id: str
    doc_id: str
    title: str
    full_content: str
    children: List[ChildChunk] = field(default_factory=list)

class BM25Index:
    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.corpus: List[ChildChunk] = []
        self.doc_lengths: List[int] = []
        self.avg_doc_len: float = 0.0
        self.doc_freqs: Dict[str, int] = {}
        self.idf: Dict[str, float] = {}
        self.inverted_index: Dict[str, List[Tuple[int, int]]] = {}

    def _tokenize(self, text: str) -> List[str]:
        return text.lower().split()

    def fit(self, chunks: List[ChildChunk]):
        self.corpus = chunks
        self.doc_lengths = [len(self._tokenize(c.content)) for c in chunks]
        self.avg_doc_len = sum(self.doc_lengths) / max(1, len(chunks))
        total_docs = len(chunks)

        for doc_idx, chunk in enumerate(chunks):
            tokens = self._tokenize(chunk.content)
            unique_tokens = set(tokens)
            for token in unique_tokens:
                self.doc_freqs[token] = self.doc_freqs.get(token, 0) + 1
            
            # Build inverted index: token -> list of (doc_idx, frequency)
            token_counts: Dict[str, int] = {}
            for token in tokens:
                token_counts[token] = token_counts.get(token, 0) + 1
            for token, count in token_counts.items():
                if token not in self.inverted_index:
                    self.inverted_index[token] = []
                self.inverted_index[token].append((doc_idx, count))

        # Precompute IDF
        for token, freq in self.doc_freqs.items():
            self.idf[token] = math.log(((total_docs - freq + 0.5) / (freq + 0.5)) + 1.0)

    def search(self, query: str, top_k: int = 50) -> List[Tuple[str, float]]:
        query_tokens = self._tokenize(query)
        scores = np.zeros(len(self.corpus))

        for token in query_tokens:
            if token not in self.inverted_index:
                continue
            token_idf = self.idf[token]
            for doc_idx, freq in self.inverted_index[token]:
                doc_len = self.doc_lengths[doc_idx]
                numerator = freq * (self.k1 + 1.0)
                denominator = freq + self.k1 * (1.0 - self.b + self.b * (doc_len / self.avg_doc_len))
                scores[doc_idx] += token_idf * (numerator / denominator)

        ranked_indices = np.argsort(-scores)[:top_k]
        return [(self.corpus[i].chunk_id, float(scores[i])) for i in ranked_indices if scores[i] > 0.0]

class VectorStore:
    def __init__(self):
        self.chunks: List[ChildChunk] = []
        self.matrix: np.ndarray = np.zeros((0, 0))

    def fit(self, chunks: List[ChildChunk]):
        self.chunks = chunks
        if not chunks:
            return
        vectors = [c.vector for c in chunks]
        # Normalize vectors for fast cosine distance via dot product
        self.matrix = np.array(vectors)
        norms = np.linalg.norm(self.matrix, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        self.matrix = self.matrix / norms

    def search(self, query_vector: np.ndarray, top_k: int = 50) -> List[Tuple[str, float]]:
        if self.matrix.shape[0] == 0:
            return []
        q_norm = query_vector / max(1e-9, np.linalg.norm(query_vector))
        similarities = np.dot(self.matrix, q_norm)
        ranked_indices = np.argsort(-similarities)[:top_k]
        return [(self.chunks[i].chunk_id, float(similarities[i])) for i in ranked_indices]

class EnterpriseHybridRAGPipeline:
    def __init__(self, rrf_k: int = 60):
        self.rrf_k = rrf_k
        self.parents: Dict[str, ParentChunk] = {}
        self.children: Dict[str, ChildChunk] = {}
        self.bm25 = BM25Index()
        self.vector_store = VectorStore()

    def ingest_parent_document(self, doc_id: str, title: str, full_text: str, child_size: int = 256, overlap: int = 32):
        words = full_text.split()
        parent_id = str(uuid.uuid4())
        parent = ParentChunk(parent_id=parent_id, doc_id=doc_id, title=title, full_content=full_text)
        
        # Segment into Child Chunks
        idx = 0
        while idx < len(words):
            end_idx = min(idx + child_size, len(words))
            child_text = " ".join(words[idx:end_idx])
            child_id = str(uuid.uuid4())
            
            # In production, call Azure OpenAI text-embedding-3-large
            # Simulated 1536-dimensional mock vector for algorithmic demonstration
            mock_vec = np.random.randn(1536).astype(np.float32)
            
            child = ChildChunk(
                chunk_id=child_id,
                parent_id=parent_id,
                content=child_text,
                tokens=end_idx - idx,
                vector=mock_vec
            )
            parent.children.append(child)
            self.children[child_id] = child
            
            if end_idx == len(words):
                break
            idx += (child_size - overlap)

        self.parents[parent_id] = parent

    def build_indices(self):
        all_children = list(self.children.values())
        self.bm25.fit(all_children)
        self.vector_store.fit(all_children)

    def retrieve(self, query: str, query_vector: np.ndarray, top_n_parents: int = 3) -> List[Dict[str, Any]]:
        # 1. Parallel retrieval across BM25 and Vector indices
        bm25_results = self.bm25.search(query, top_k=50)
        vector_results = self.vector_store.search(query_vector, top_k=50)

        # 2. Reciprocal Rank Fusion (RRF)
        rrf_scores: Dict[str, float] = {}

        for rank, (chunk_id, _) in enumerate(bm25_results):
            rrf_scores[chunk_id] = rrf_scores.get(chunk_id, 0.0) + (1.0 / (self.rrf_k + (rank + 1)))

        for rank, (chunk_id, _) in enumerate(vector_results):
            rrf_scores[chunk_id] = rrf_scores.get(chunk_id, 0.0) + (1.0 / (self.rrf_k + (rank + 1)))

        # 3. Sort by fused RRF score
        sorted_chunks = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)

        # 4. Context Expansion: Resolve winning children to unique Parent Chunks
        seen_parents = set()
        retrieved_contexts = []

        for chunk_id, score in sorted_chunks:
            child = self.children[chunk_id]
            parent_id = child.parent_id
            if parent_id not in seen_parents:
                seen_parents.add(parent_id)
                parent = self.parents[parent_id]
                retrieved_contexts.append({
                    "parent_id": parent.parent_id,
                    "title": parent.title,
                    "matched_child_id": chunk_id,
                    "rrf_score": score,
                    "full_context": parent.full_content
                })
                if len(retrieved_contexts) >= top_n_parents:
                    break

        return retrieved_contexts
