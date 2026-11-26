import numpy as np
from typing import List, Dict, Any

class ExemplarRecord:
    def __init__(self, exemplar_id: str, query: str, output_text: str, embedding: List[float]):
        self.exemplar_id = exemplar_id
        self.query = query
        self.output_text = output_text
        self.embedding = np.array(embedding, dtype=np.float32)

class VectorKNNExemplarStore:
    def __init__(self, exemplars: List[ExemplarRecord]):
        self.exemplars = exemplars

    def find_top_k(self, query_embedding: List[float], k: int = 3) -> List[ExemplarRecord]:
        q_vec = np.array(query_embedding, dtype=np.float32)
        q_norm = np.linalg.norm(q_vec)
        if q_norm == 0:
            return self.exemplars[:k]

        similarities = []
        for ex in self.exemplars:
            ex_norm = np.linalg.norm(ex.embedding)
            sim = np.dot(q_vec, ex.embedding) / (q_norm * ex_norm + 1e-9)
            similarities.append((sim, ex))

        similarities.sort(key=lambda item: item[0], reverse=True)
        return [item[1] for item in similarities[:k]]

    def assemble_dynamic_few_shot_block(self, top_k_exemplars: List[ExemplarRecord]) -> str:
        blocks = []
        for ex in top_k_exemplars:
            blocks.append(
                f"<example id=\"{ex.exemplar_id}\">\n"
                f"<input>{ex.query}</input>\n"
                f"<output>{ex.output_text}</output>\n"
                f"</example>"
            )
        return "<verified_exemplars>\n" + "\n\n".join(blocks) + "\n</verified_exemplars>"
