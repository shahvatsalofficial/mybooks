import heapq

class PrioritizedTask(BaseModel):
    priority_level: int = Field(ge=1, le=5, description="1: Highest Executive SLA, 5: Low Background")
    task_id: str
    task_name: str
    estimated_tokens: int
    created_at: float = Field(default_factory=time.time)

    def __lt__(self, other: "PrioritizedTask") -> bool:
        # Lower priority_level number indicates higher scheduling precedence
        if self.priority_level == other.priority_level:
            return self.created_at < other.created_at
        return self.priority_level < other.priority_level

class SwarmPriorityDispatcher:
    def __init__(self):
        self._queue: List[PrioritizedTask] = []

    def submit_task(self, task: PrioritizedTask):
        heapq.heappush(self._queue, task)
        print(f"[PRIORITY QUEUE] Enqueued {task.task_id} (Level {task.priority_level}: '{task.task_name}'). Queue Depth: {len(self._queue)}")

    def dispatch_next(self) -> Optional[PrioritizedTask]:
        if not self._queue:
            return None
        task = heapq.heappop(self._queue)
        print(f"[PRIORITY DISPATCH] Routing Priority {task.priority_level} Task: '{task.task_name}'")
        return task
