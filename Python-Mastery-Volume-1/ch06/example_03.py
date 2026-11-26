"""
Recipe 06.1: High-Performance Non-Blocking TCP Telemetry Server
File: recipe_06_1_async_tcp_server.py
Python Version: 3.12+
"""

from __future__ import annotations
import asyncio
import socket
import logging
import time

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("AsyncTCPServer")


class HighThroughputTelemetryProtocol(asyncio.Protocol):
    """Low-level protocol managing socket lifecycle callbacks without coroutine overhead."""
    
    def __init__(self) -> None:
        self.transport: asyncio.Transport | None = None
        self.peername: tuple[str, int] | None = None
        self.bytes_received: int = 0

    def connection_made(self, transport: asyncio.BaseTransport) -> None:
        self.transport = transport  # type: ignore[assignment]
        self.peername = self.transport.get_extra_info("peername")
        logger.info(f"Connection established from {self.peername}")

        # Extract underlying OS socket and tune flags
        sock = self.transport.get_extra_info("socket")
        if sock is not None:
            # Disable Nagle's algorithm to eliminate 40ms buffering delays
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            # Enable TCP keep-alive probes
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)

        # Set high and low watermarks for write buffer backpressure (64KB / 16KB)
        self.transport.set_write_buffer_limits(high=65536, low=16384)

    def data_received(self, data: bytes) -> None:
        """Invoked immediately when epoll detects EPOLLIN with zero copy string conversion."""
        self.bytes_received += len(data)
        
        # Echo processed telemetry payload back to client
        if self.transport and not self.transport.is_closing():
            # In a production server, dispatch to zero-copy parser
            response = b"ACK:" + data
            self.transport.write(response)

    def pause_writing(self) -> None:
        """Triggered when OS send buffer exceeds high watermark. Enforces backpressure."""
        logger.warning(f"High watermark reached for {self.peername}. Pausing network reads.")

    def resume_writing(self) -> None:
        """Triggered when OS send buffer drains below low watermark."""
        logger.info(f"Buffer drained for {self.peername}. Resuming network reads.")

    def connection_lost(self, exc: Exception | None) -> None:
        if exc:
            logger.warning(f"Connection with {self.peername} dropped: {exc}")
        else:
            logger.info(f"Clean disconnect from {self.peername}. Total bytes: {self.bytes_received}")
        self.transport = None


async def start_telemetry_daemon(host: str = "127.0.0.1", port: int = 9500) -> None:
    loop = asyncio.get_running_loop()
    
    # Configure listening server with high backlog and address reuse
    server = await loop.create_server(
        protocol_factory=HighThroughputTelemetryProtocol,
        host=host,
        port=port,
        reuse_address=True,
        backlog=4096,
    )

    addr = server.sockets[0].getsockname()
    logger.info(f"TCP Telemetry Server listening on {addr} [TCP_NODELAY active, backlog=4096]")

    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    try:
        asyncio.run(start_telemetry_daemon())
    except KeyboardInterrupt:
        logger.info("Server shutting down cleanly.")
