from typing import Dict, Any, List

class DeadLetterQueueGovernor:
    def __init__(self, max_retries: int = 3):
        self.max_retries = max_retries
        self.retry_counts: Dict[str, int] = {}
        self.dead_letter_vault: List[Dict[str, Any]] = []

    def handle_processing_failure(self, task_id: str, raw_message: str, error_msg: str) -> None:
        count = self.retry_counts.get(task_id, 0) + 1
        self.retry_counts[task_id] = count

        if count >= self.max_retries:
            print(f"[DLQ GOVERNOR] Task '{task_id}' exceeded max retries ({count}/{self.max_retries})! Evicting to DLQ.")
            self.dead_letter_vault.append({
                "task_id": task_id,
                "payload": raw_message,
                "error": error_msg,
                "quarantine_status": "LOCKED"
            })
            del self.retry_counts[task_id]
        else:
            print(f"[RETRY GOVERNOR] Task '{task_id}' retry {count}/{self.max_retries} scheduled with backoff.")

dlq = DeadLetterQueueGovernor(max_retries=3)
dlq.handle_processing_failure("TASK_CORRUPT_01", "{"bad_json": ", "JSONDecodeError")
dlq.handle_processing_failure("TASK_CORRUPT_01", "{"bad_json": ", "JSONDecodeError")
dlq.handle_processing_failure("TASK_CORRUPT_01", "{"bad_json": ", "JSONDecodeError")
print(f"Quarantined DLQ Entries: {len(dlq.dead_letter_vault)}")
