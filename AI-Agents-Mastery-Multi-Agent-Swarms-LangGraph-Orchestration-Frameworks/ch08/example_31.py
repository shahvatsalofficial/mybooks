# Hardened Grounding Verification Gate:
def verify_claim_provenance(claim_text: str, verified_sources: List[str]) -> bool:
    """Blocks ungrounded upstream claims from propagating downstream."""
    is_grounded = any(source.lower() in claim_text.lower() for source in verified_sources)
    if not is_grounded:
        raise ValueError(f"UNGROUNDED CLAIM DETECTED: '{claim_text}' has no verified citation in source data!")
    return True
