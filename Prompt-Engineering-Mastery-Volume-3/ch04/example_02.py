"""
Mathematical Memory Decay Engine: Computes composite retrieval scores
incorporating exponential temporal decay, intrinsic importance, and cosine similarity.
"""

import math
import time
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass, field


@dataclass
class MemoryRecord:
    memory_id: str
    content: str
    embedding: List[float]
    importance: float  # [0.0, 1.0]
    created_at: float  # Epoch timestamp
    last_accessed_at: float  # Epoch timestamp
    access_count: int = 1
    metadata: Dict[str, Any] = field(default_factory=dict)


class MemoryScoringEngine:
    """Calculates multi-dimensional memory relevance scores with exponential decay."""

    def __init__(
        self,
        decay_half_life_hours: float = 72.0,
        weight_recency: float = 0.25,
        weight_importance: float = 0.35,
        weight_similarity: float = 0.40,
    ):
        self.decay_lambda = math.log(2) / (decay_half_life_hours * 3600.0)
        self.w_recency = weight_recency
        self.w_importance = weight_importance
        self.w_similarity = weight_similarity

        assert math.isclose(
            self.w_recency + self.w_importance + self.w_similarity, 1.0, abs_tol=1e-5
        ), "Weights must sum to 1.0"

    def calculate_cosine_similarity(self, vec_a: List[float], vec_b: List[float]) -> float:
        """Computes cosine similarity between two dense embedding vectors."""
        if len(vec_a) != len(vec_b):
            raise ValueError("Embedding dimension mismatch.")

        dot_product = sum(a * b for a, b in zip(vec_a, vec_b))
        norm_a = math.sqrt(sum(a * a for a in vec_a))
        norm_b = math.sqrt(sum(b * b for b in vec_b))

        if norm_a == 0.0 or norm_b == 0.0:
            return 0.0
        return dot_product / (norm_a * norm_b)

    def calculate_recency_score(self, last_accessed_timestamp: float, current_timestamp: float) -> float:
        """Computes exponential temporal decay score."""
        delta_seconds = max(0.0, current_timestamp - last_accessed_timestamp)
        return math.exp(-self.decay_lambda * delta_seconds)

    def score_memory(
        self,
        memory: MemoryRecord,
        query_embedding: List[float],
        current_timestamp: float,
    ) -> float:
        """Computes holistic composite score S(m, q, t)."""
        sim_score = self.calculate_cosine_similarity(memory.embedding, query_embedding)
        recency_score = self.calculate_recency_score(memory.last_accessed_at, current_timestamp)
        importance_score = min(max(memory.importance, 0.0), 1.0)

        composite_score = (
            (self.w_similarity * sim_score)
            + (self.w_recency * recency_score)
            + (self.w_importance * importance_score)
        )
        return composite_score

    def rank_memories(
        self,
        memories: List[MemoryRecord],
        query_embedding: List[float],
        top_k: int = 5,
    ) -> List[Tuple[MemoryRecord, float]]:
        """Ranks candidate memories and updates access timestamps."""
        now = time.time()
        scored_pairs = []

        for mem in memories:
            score = self.score_memory(mem, query_embedding, now)
            scored_pairs.append((mem, score))

        scored_pairs.sort(key=lambda x: x[1], reverse=True)
        top_results = scored_pairs[:top_k]

        for mem, _ in top_results:
            mem.last_accessed_at = now
            mem.access_count += 1

        return top_results
