import threading

class LockLeaseHeartbeat:
    def __init__(self, resource_name: str, renewal_interval: float = 2.0):
        self.resource_name = resource_name
        self.interval = renewal_interval
        self._stop_event = threading.Event()
        self._thread = None

    def start(self):
        self._thread = threading.Thread(target=self._heartbeat_loop)
        self._thread.daemon = True
        self._thread.start()
        print(f"[HEARTBEAT] Started lease renewal thread for '{self.resource_name}'.")

    def _heartbeat_loop(self):
        while not self._stop_event.is_set():
            time.sleep(self.interval)
            if not self._stop_event.is_set():
                print(f"[HEARTBEAT] Extending TTL lease for '{self.resource_name}' by 5s...")

    def stop(self):
        self._stop_event.set()
        if self._thread:
            self._thread.join()
        print(f"[HEARTBEAT] Stopped lease renewal for '{self.resource_name}'.")
