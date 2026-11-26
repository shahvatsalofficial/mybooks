"""
Recipe 04.3: Enterprise Graceful Shutdown Coordinator
File: recipe_04_3_graceful_shutdown.py
Python Version: 3.12+
"""

from __future__ import annotations
import asyncio
import logging
import signal
import sys
import time

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("ShutdownCoordinator")


class GracefulServer:
    def __init__(self, port: int = 8080) -> None:
        self.port = port
        self.is_running = True
        self.active_tasks: set[asyncio.Task[None]] = set()
        self.shutdown_event = asyncio.Event()

    async def handle_client_connection(self, client_id: int) -> None:
        """Simulates processing a long-lived client connection."""
        try:
            logger.info(f"[Conn-{client_id}] Connection opened. Processing transactions...")
            while self.is_running:
                await asyncio.sleep(0.5)
                logger.info(f"[Conn-{client_id}] Heartbeat ping sent.")
        except asyncio.CancelledError:
            logger.info(f"[Conn-{client_id}] CancelledError caught. Flushing socket buffers...")
            await asyncio.sleep(0.1)  # Clean async teardown
            raise  # Re-raise to acknowledge cancellation
        finally:
            logger.info(f"[Conn-{client_id}] Connection cleanly closed.")

    async def run(self) -> None:
        logger.info(f"Server listening on port {self.port}. Spawning worker connections...")
        client_seq = 0

        # Register OS signal handlers (Unix/Linux/macOS)
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                loop.add_signal_handler(sig, self._handle_signal, sig)
            except NotImplementedError:
                # Windows fallback (signals are emulated differently)
                pass

        # Background simulator creating active client sessions
        while not self.shutdown_event.is_set():
            client_seq += 1
            task = asyncio.create_task(self.handle_client_connection(client_seq))
            self.active_tasks.add(task)
            task.add_done_callback(self.active_tasks.discard)

            if client_seq >= 5:
                # After spawning 5 clients, trigger simulated shutdown for demonstration
                logger.info("Simulation threshold reached: Initiating graceful termination.")
                self.shutdown_event.set()
                break

            await asyncio.sleep(0.2)

        # Trigger coordinated shutdown
        await self.shutdown(timeout_sec=3.0)

    def _handle_signal(self, sig: signal.Signals) -> None:
        logger.warning(f"Received OS signal {sig.name}. Triggering shutdown sequence...")
        self.shutdown_event.set()

    async def shutdown(self, timeout_sec: float = 3.0) -> None:
        """Executes the two-phase graceful drain and cancellation protocol."""
        logger.info("Phase 1: Halting new connections and setting shutdown flags.")
        self.is_running = False

        if not self.active_tasks:
            logger.info("Zero active connections. Clean shutdown complete.")
            return

        logger.info(f"Phase 2: Draining {len(self.active_tasks)} active tasks with {timeout_sec}s deadline...")
        
        # Broadcast cancellation to all currently running tasks
        for task in self.active_tasks:
            task.cancel(msg="Server graceful shutdown initiated")

        # Wait for all tasks to acknowledge cancellation within the deadline
        try:
            async with asyncio.timeout(timeout_sec):
                # Return exceptions to prevent gather from crashing on CancelledError
                await asyncio.gather(*self.active_tasks, return_exceptions=True)
            logger.info("All active tasks successfully drained and terminated.")
        except TimeoutError:
            logger.critical(f"Shutdown deadline exceeded! {len(self.active_tasks)} tasks forcibly dropped.")


if __name__ == "__main__":
    server = GracefulServer(port=9000)
    asyncio.run(server.run())
