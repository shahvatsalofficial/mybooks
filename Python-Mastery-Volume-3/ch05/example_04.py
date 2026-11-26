# DEFECTIVE RETRY IMPLEMENTATION (PRE-INCIDENT)
async def verify_fraud(transaction_id: str, payload: dict) -> dict:
    for attempt in range(5):  # CRITICAL FLAW: 5 immediate retries!
        try:
            # Synchronous-like tight retry loop with zero backoff and zero jitter!
            return await http_client.post("https://api.fraud-vendor.internal/verify", json=payload, timeout=3.0)
        except httpx.TimeoutException:
            # Retries IMMEDIATELY upon timeout!
            logger.warning("Fraud check timed out. Retrying immediately...")
            continue
    raise FraudCheckFailed("Fraud API completely unavailable.")
