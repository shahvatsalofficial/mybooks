# semantic_diff.py
"""
Computes behavioral semantic difference between two prompt versions.
Generates a test report showing how LLM outputs change across golden dataset.
"""
from sentence_transformers import SentenceTransformer
import numpy as np


def compute_prompt_semantic_diff(
    prompt_v_old: str,
    prompt_v_new: str,
    test_inputs: list[str],
    llm_fn_old,
    llm_fn_new
) -> dict:
    """
    Compares behavioral impact of two prompt versions across test inputs.
    Returns similarity scores and flagged divergent cases.
    """
    model = SentenceTransformer("all-mpnet-base-v2")
    divergent_cases = []
    similarities = []

    for query in test_inputs:
        out_old = llm_fn_old(prompt_v_old, query)
        out_new = llm_fn_new(prompt_v_new, query)

        emb_old = model.encode(out_old)
        emb_new = model.encode(out_new)

        cos_sim = float(np.dot(emb_old, emb_new) / (
            np.linalg.norm(emb_old) * np.linalg.norm(emb_new)
        ))
        similarities.append(cos_sim)

        if cos_sim < 0.85:  # Flag cases where outputs diverge significantly
            divergent_cases.append({
                "query": query,
                "similarity": round(cos_sim, 4),
                "old_output": out_old[:300],
                "new_output": out_new[:300]
            })

    return {
        "avg_similarity": round(float(np.mean(similarities)), 4),
        "min_similarity": round(float(np.min(similarities)), 4),
        "divergent_count": len(divergent_cases),
        "divergent_cases": divergent_cases,
        "recommendation": (
            "SAFE TO MERGE" if float(np.mean(similarities)) > 0.88
            else "REVIEW REQUIRED — behavioral drift detected"
        )
    }
