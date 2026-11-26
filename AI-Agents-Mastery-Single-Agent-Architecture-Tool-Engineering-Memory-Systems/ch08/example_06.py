@dataclass
class FailedTrajectoryRecord:
    session_id: str
    error_message: str
    turn_count: int
    memory_dump: List[Dict[str, str]]
    timestamp: float

class DeadLetterQueue:
    def __init__(self, dlq_file_path: str):
        self.path = dlq_file_path

    def route_to_dlq(self, session_id: str, error: str, turn: int, memory: List[Dict[str, str]]):
        record = FailedTrajectoryRecord(
            session_id=session_id,
            error_message=error,
            turn_count=turn,
            memory_dump=memory,
            timestamp=time.time()
        )
        
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record.__dict__) + "
")
            
        print(f"[DLQ ALERT] Session {session_id} failed at turn {turn}: {error}. Routed to triage.")

# Verification
dlq = DeadLetterQueue("/tmp/agent_failures.dlq")
dlq.route_to_dlq("sess_991", "Context length exceeded (128k)", 12, [{"role": "user", "content": "analyze"}])
