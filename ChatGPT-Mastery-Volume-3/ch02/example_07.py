# corrective_rag_evaluator.py — Self-Reflective Retrieval Filter
from typing import Dict, Any, List
import json

class CorrectiveRAGEvaluator:
    def __init__(self, evaluator_model):
        self.model = evaluator_model

    def evaluate_retrieval(self, query: str, context_chunks: List[str]) -> Dict[str, Any]:
        """
        Evaluates retrieved chunks and returns: 'CORRECT', 'AMBIGUOUS', or 'INCORRECT'.
        """
        prompt = f"""
        User Query: {query}
        Retrieved Documents:
        {chr(10).join([f'[{i}] {c}' for i, c in enumerate(context_chunks)])}

        Evaluate whether the retrieved documents contain sufficient, relevant information to answer the query.
        Return JSON:
        {{
            "decision": "CORRECT" | "AMBIGUOUS" | "INCORRECT",
            "confidence_score": 0.0 to 1.0,
            "rationale": "string explanation"
        }}
        """
        response = self.model.generate_json(prompt)
        decision = response.get("decision", "INCORRECT")
        confidence = response.get("confidence_score", 0.0)

        if decision == "CORRECT" and confidence >= 0.85:
            return {"action": "PROCEED", "chunks": context_chunks}
        elif decision == "AMBIGUOUS":
            refined = self._refine_chunks(query, context_chunks)
            return {"action": "AUGMENT", "chunks": refined}
        else:
            return {"action": "FALLBACK_OR_ABORT", "chunks": []}

    def _refine_chunks(self, query: str, chunks: List[str]) -> List[str]:
        # Strips sentences that do not mention key query entities
        refined = []
        q_terms = set(query.lower().split())
        for c in chunks:
            sentences = c.split(". ")
            kept = [s for s in sentences if any(t in s.lower() for t in q_terms)]
            if kept:
                refined.append(". ".join(kept))
        return refined
