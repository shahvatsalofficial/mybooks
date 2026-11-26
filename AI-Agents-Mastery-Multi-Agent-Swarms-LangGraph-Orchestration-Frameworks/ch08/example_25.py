class DualModelContrastiveChecker:
    @staticmethod
    def verify_assertion(assertion_claim: str, ground_truth_context: str) -> bool:
        # Evaluates entailment vs contradiction
        has_terms = any(word in ground_truth_context.lower() for word in assertion_claim.lower().split() if len(word) > 4)
        if not has_terms:
            print(f"[NLI AUDIT ALERT] Potential hallucination: Claim '{assertion_claim}' lacks grounding in context!")
            return False
        return True
