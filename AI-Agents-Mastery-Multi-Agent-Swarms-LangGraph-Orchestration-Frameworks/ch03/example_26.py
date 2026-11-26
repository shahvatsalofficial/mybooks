def conservative_adjudication_reducer(current_val: str, new_val: str) -> str:
    """Fail-safe reducer: REJECT or FRAUD always overrides APPROVE."""
    priority_order = {"FLAG_FRAUD": 3, "REJECT": 2, "PENDING": 1, "APPROVE": 0}
    curr_score = priority_order.get(current_val, 0)
    new_score = priority_order.get(new_val, 0)
    
    # Return whichever decision has higher risk severity
    return current_val if curr_score >= new_score else new_val

class ConcurrentInsuranceState(TypedDict):
    claim_id: str
    audit_decision: Annotated[str, conservative_adjudication_reducer]
