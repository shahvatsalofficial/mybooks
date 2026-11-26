import json
from typing import Dict, Any, List

class FaithfulnessEvaluator:
    """Evaluates whether an agent's synthesized response is strictly grounded in retrieved context."""

    EVAL_PROMPT = """
You are an expert AI quality auditor. Evaluate the following AGENT RESPONSE against the RETRIEVED CONTEXT.
Identify whether all factual claims made in the response are directly supported by the context.

RETRIEVED CONTEXT:
{context}

AGENT RESPONSE:
{response}

Emit a JSON object with two fields:
- "is_faithful": boolean (true if all claims are supported, false if ungrounded claims exist)
- "hallucinated_claims": list of strings (empty if none)
- "faithfulness_score": float between 0.0 and 1.0
"""

    @classmethod
    def evaluate(cls, context_docs: List[str], agent_response: str) -> Dict[str, Any]:
        """Simulates rigorous LLM evaluation of response groundedness."""
        # Mock evaluation logic for deterministic testing
        combined_context = " ".join(context_docs)
        
        # Check for ungrounded claims (demonstration check)
        if "hallucinated" in agent_response.lower():
            return {
                "is_faithful": False,
                "hallucinated_claims": ["Agent claimed 99.999% SLA not found in reference documents."],
                "faithfulness_score": 0.40
            }
            
        return {
            "is_faithful": True,
            "hallucinated_claims": [],
            "faithfulness_score": 0.98
        }

if __name__ == "__main__":
    docs = [
        "Kubernetes deployment payment-svc specifies 4 replicas in us-east-1.",
        "Average memory utilization over the last 24 hours was 1.2 GB per pod."
    ]
    good_resp = "The payment-svc deployment runs 4 replicas in us-east-1 with 1.2 GB memory per pod."
    
    res = FaithfulnessEvaluator.evaluate(docs, good_resp)
    print("Faithfulness Evaluation Result:")
    print(json.dumps(res, indent=2))
