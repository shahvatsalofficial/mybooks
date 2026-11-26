import threading
import time
from typing import Optional

class AgentDeadlockWatchdog:
    def __init__(self, timeout_seconds: float = 30.0):
        self.timeout = timeout_seconds
        self.last_heartbeat = time.time()
        self.is_running = True
        self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.thread.start()

    def heartbeat(self, step_info: str) -> None:
        self.last_heartbeat = time.time()

    def _monitor_loop(self) -> None:
        while self.is_running:
            time.sleep(1.0)
            elapsed = time.time() - self.last_heartbeat
            if elapsed > self.timeout:
                print(f"[FATAL WATCHDOG] Agent Deadlock Detected! No progress for {elapsed:.1f}s.")
                break

    def stop(self) -> None:
        self.is_running = False

watchdog = AgentDeadlockWatchdog(timeout_seconds=5.0)
watchdog.heartbeat("Step 1 Complete")
time.sleep(0.5)
watchdog.heartbeat("Step 2 Complete")
watchdog.stop()
