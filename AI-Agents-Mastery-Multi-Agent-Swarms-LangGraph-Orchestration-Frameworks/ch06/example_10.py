class DeadLetterInspector:
    def __init__(self):
        self.quarantined_messages: List[Dict[str, Any]] = []

    def inspect_and_quarantine(self, raw_payload: str, error_reason: str):
        print(f"[DLQ] Poison pill detected! Quarantining: {error_reason}")
        self.quarantined_messages.append({
            "timestamp": time.time(),
            "payload": raw_payload,
            "error": error_reason
        })
