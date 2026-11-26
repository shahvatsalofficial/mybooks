import time
from typing import Dict, Any, List

class WorkerHeartbeatManager:
    """Tracks worker liveness and reclaims orphaned agent missions."""

    def __init__(self, timeout_threshold_seconds: int = 45):
        self.threshold = timeout_threshold_seconds
        self.registry: Dict[str, float] = {}

    def record_heartbeat(self, task_id: str) -> None:
        """Worker calls this method every N seconds while active."""
        self.registry[task_id] = time.time()

    def reap_orphaned_tasks(self, current_time: float) -> List[str]:
        """Watchdog scanner that identifies dead tasks for rescheduling."""
        orphaned = []
        for task_id, last_beat in list(self.registry.items()):
            if current_time - last_beat > self.threshold:
                orphaned.append(task_id)
                del self.registry[task_id]
        return orphaned

if __name__ == "__main__":
    hb = WorkerHeartbeatManager(timeout_threshold_seconds=15)
    t0 = time.time()
    
    # Worker 1 beats at t=0
    hb.record_heartbeat("TASK_ALIVE_1")
    # Worker 2 beats at t=0 but then crashes
    hb.record_heartbeat("TASK_CRASHED_2")
    
    # 20 seconds later...
    dead_tasks = hb.reap_orphaned_tasks(t0 + 20)
    print("Orphaned tasks detected by reaper:", dead_tasks)
