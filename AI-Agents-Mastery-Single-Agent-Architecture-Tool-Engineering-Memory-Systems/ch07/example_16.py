from typing import Dict, Any

class FeedbackTelemetryCollector:
    def __init__(self):
        self.feedback_store: Dict[str, Dict[str, Any]] = {}

    def log_feedback(self, trace_id: str, is_positive: bool, correction_note: str = "") -> None:
        self.feedback_store[trace_id] = {
            "thumb": "UP" if is_positive else "DOWN",
            "correction": correction_note,
            "exported_to_prometheus": True
        }
        print(f"[FEEDBACK] Registered {self.feedback_store[trace_id]['thumb']} for trace '{trace_id}'")

collector = FeedbackTelemetryCollector()
collector.log_feedback("TRC-4819", is_positive=True)
collector.log_feedback("TRC-4820", is_positive=False, correction_note="Agent called SQL tool 4 times redundantly")
