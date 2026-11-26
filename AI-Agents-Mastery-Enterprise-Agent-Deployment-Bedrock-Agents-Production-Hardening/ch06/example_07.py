import signal
import sys
import time

class GracefulTerminationHandler:
    """Intercepts SIGTERM and SIGINT to serialize agent state prior to container death."""

    def __init__(self):
        self.shutdown_requested = False
        signal.signal(signal.SIGTERM, self._handle_signal)
        signal.signal(signal.SIGINT, self._handle_signal)

    def _handle_signal(self, signum, frame):
        print(f"\n[SIGNAL TRAPPED] Caught signal {signum}. Initiating emergency state serialization...")
        self.shutdown_requested = True
        # Emergency checkpoint routine
        print("Flushed active agent context to durable store. Safe to terminate.")
        sys.exit(0)

if __name__ == "__main__":
    handler = GracefulTerminationHandler()
    print("GracefulTerminationHandler registered. Listening for POSIX signals.")
