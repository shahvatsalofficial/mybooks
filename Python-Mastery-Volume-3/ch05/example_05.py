# REMEDIATED RESILIENT CLIENT CALL
async def verify_fraud_resilient(transaction_id: str, payload: dict) -> dict:
    # Protected by Circuit Breaker with local heuristic fallback
    return await fraud_circuit_breaker.call(
        _execute_fraud_http_call,
        payload,
        fallback=_local_rule_based_fallback,
    )
