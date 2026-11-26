class SwarmSpanTracer:
    def __init__(self, trace_id: str, span_name: str, agent_role: str, parent_span_id: Optional[str] = None):
        self.trace_id = trace_id
        self.span_id = str(uuid.uuid4())
        self.parent_span_id = parent_span_id
        self.span_name = span_name
        self.agent_role = agent_role
        self.start_time = 0.0
        self.end_time = 0.0
        self.metadata: Dict[str, Any] = {}

    def __enter__(self):
        self.start_time = time.time()
        print(f"[TRACE SPAN START] [{self.agent_role}] {self.span_name} (Span: {self.span_id[:8]}... Parent: {str(self.parent_span_id)[:8]}...)")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.time()
        duration_ms = (self.end_time - self.start_time) * 1000
        status = "ERROR" if exc_type else "SUCCESS"
        print(f"[TRACE SPAN END] [{self.agent_role}] {self.span_name} - {status} ({duration_ms:.2f}ms)")
