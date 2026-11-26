"""
Dual-Pass Factuality Verifier Engine.
Decouples generation from verification, decomposing draft outputs into atomic claims
and verifying each claim against source document chunks using Natural Language Inference.
"""

from typing import List, Dict, Any, Tuple
import json
import re


class FactualityVerificationError(Exception):
    """Raised when an agent output fails grounding standards."""
    pass


class DualPassFactualityVerifier:
    """Audits candidate agent outputs against raw source reference documents."""

    def __init__(self, nli_evaluator_client: Any, min_faithfulness_score: float = 0.95):
        self.nli_client = nli_evaluator_client
        self.min_score = min_faithfulness_score

    def extract_atomic_claims(self, draft_text: str) -> List[str]:
        """
        Decomposes complex prose into atomic propositions using decomposition prompt.
        """
        decomposition_prompt = f"""
Decompose the following text into a JSON array of atomic factual claims.
Each claim must be an isolated, single-fact proposition.
Do not include subjective opinions or conversational phrases.

<text_to_decompose>
{draft_text}
</text_to_decompose>

Output MUST be a valid JSON array of strings:
["Claim 1", "Claim 2", ...]
"""
        response = self.nli_client.generate(decomposition_prompt)
        try:
            claims = json.loads(response)
            return [c.strip() for c in claims if isinstance(c, str) and c.strip()]
        except json.JSONDecodeError:
            sentences = re.split(r"[.!?]\s+", draft_text)
            return [s.strip() for s in sentences if len(s.strip()) > 10]

    def verify_claim_against_corpus(
        self,
        claim: str,
        source_documents: List[Dict[str, str]]
    ) -> Tuple[bool, Optional[str]]:
        """
        Evaluates whether an individual claim is mathematically entailed by any source chunk.
        """
        for doc in source_documents:
            chunk_text = doc["content"]
            chunk_id = doc["chunk_id"]

            eval_prompt = f"""
You are a Strict Factual Entailment Verifier.
Premise: {chunk_text}
Hypothesis: {claim}

Does the Premise explicitly entail and prove the Hypothesis?
Answer strictly with JSON:
{{"entailed": true}} or {{"entailed": false, "reason": "..."}}
"""
            raw_eval = self.nli_client.generate(eval_prompt)
            try:
                res = json.loads(raw_eval)
                if res.get("entailed") is True:
                    return True, chunk_id
            except json.JSONDecodeError:
                continue

        return False, None

    def audit_draft_output(
        self,
        draft_text: str,
        source_documents: List[Dict[str, str]]
    ) -> Tuple[bool, float, List[Dict[str, Any]]]:
        """
        Executes exhaustive audit across all atomic claims.
        Returns: (passes_firewall, faithfulness_ratio, audit_telemetry)
        """
        claims = self.extract_atomic_claims(draft_text)
        if not claims:
            return True, 1.0, []

        verified_count = 0
        telemetry = []

        for claim in claims:
            is_entailed, matching_chunk = self.verify_claim_against_corpus(claim, source_documents)
            if is_entailed:
                verified_count += 1
                telemetry.append({"claim": claim, "status": "VERIFIED", "source_chunk": matching_chunk})
            else:
                telemetry.append({"claim": claim, "status": "UNGROUNDED", "source_chunk": None})

        faithfulness_ratio = verified_count / len(claims)
        passes_firewall = faithfulness_ratio >= self.min_score

        return passes_firewall, faithfulness_ratio, telemetry
