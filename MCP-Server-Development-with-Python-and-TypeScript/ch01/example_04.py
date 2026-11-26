"""
Filename: mcp_wire_multiplexer.py
Description: Production Asynchronous JSON-RPC 2.0 Multiplexer for MCP stdio transports.
Author: Vatsal Shah (MCP Mastery Series)
Dependencies: Python 3.11+, pydantic v2
"""

import asyncio
import json
import logging
import sys
from typing import Any, Callable, Coroutine, Dict, Optional
from pydantic import BaseModel, Field, ValidationError

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("MCP.Multiplexer")


class JSONRPCRequest(BaseModel):
    jsonrpc: str = Field(..., pattern=r"^2\.0$")
    id: Optional[str | int] = None
    method: str
    params: Optional[Dict[str, Any]] = None


class JSONRPCResponse(BaseModel):
    jsonrpc: str = "2.0"
    id: str | int
    result: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None


class MCPWireMultiplexer:
    """Manages full-duplex JSON-RPC 2.0 message dispatch over standard I/O."""

    def __init__(self, max_buffer_bytes: int = 10 * 1024 * 1024):
        self._max_buffer = max_buffer_bytes
        self._pending_requests: Dict[str | int, asyncio.Future] = {}
        self._method_handlers: Dict[str, Callable[[Optional[Dict[str, Any]]], Coroutine]] = {}
        self._running = False

    def register_handler(
        self, method: str, handler: Callable[[Optional[Dict[str, Any]]], Coroutine]
    ) -> None:
        """Register an async handler for a given MCP method."""
        self._method_handlers[method] = handler
        logger.debug(f"Registered method handler: {method}")

    async def start(self) -> None:
        """Initialize the stdin reader loop."""
        self._running = True
        loop = asyncio.get_running_loop()
        reader = asyncio.StreamReader(limit=self._max_buffer)
        protocol = asyncio.StreamReaderProtocol(reader)
        await loop.connect_read_pipe(lambda: protocol, sys.stdin)

        logger.info("MCP Wire Multiplexer started on stdio.")
        try:
            while self._running:
                line = await reader.readline()
                if not line:
                    logger.info("stdin closed by Host. Initiating clean termination.")
                    break
                asyncio.create_task(self._process_raw_line(line))
        except asyncio.CancelledError:
            logger.info("Multiplexer loop cancelled.")
        finally:
            self._running = False

    async def send_response(self, response: JSONRPCResponse) -> None:
        """Serialize and write a JSON-RPC response to stdout."""
        payload = response.model_dump_json(exclude_none=True) + "\n"
        sys.stdout.write(payload)
        sys.stdout.flush()

    async def send_notification(self, method: str, params: Optional[Dict[str, Any]] = None) -> None:
        """Send a one-way notification (strictly without ID)."""
        envelope = {"jsonrpc": "2.0", "method": method}
        if params is not None:
            envelope["params"] = params
        payload = json.dumps(envelope) + "\n"
        sys.stdout.write(payload)
        sys.stdout.flush()

    async def _process_raw_line(self, raw_bytes: bytes) -> None:
        """Parse raw line buffer into validated JSON-RPC message."""
        try:
            raw_text = raw_bytes.decode("utf-8").strip()
            if not raw_text:
                return

            data = json.loads(raw_text)

            # Check if this is an incoming response to a client-initiated request
            if "id" in data and ("result" in data or "error" in data):
                req_id = data["id"]
                if req_id in self._pending_requests:
                    future = self._pending_requests.pop(req_id)
                    if not future.done():
                        future.set_result(data)
                return

            # Otherwise, validate incoming request or notification
            req = JSONRPCRequest.model_validate(data)

            if req.id is not None:
                # It is a Request expecting response
                await self._dispatch_request(req)
            else:
                # It is a Notification (fire-and-forget)
                await self._dispatch_notification(req)

        except json.JSONDecodeError as err:
            logger.error(f"JSON Parse Error: {err}")
            await self._send_raw_error(None, -32700, "Parse error: Invalid JSON")
        except ValidationError as val_err:
            logger.error(f"Schema Validation Error: {val_err}")
            await self._send_raw_error(None, -32600, "Invalid Request: Malformed JSON-RPC envelope")
        except Exception as general_err:
            logger.exception(f"Unhandled exception processing wire frame: {general_err}")
            await self._send_raw_error(None, -32603, "Internal server error")

    async def _dispatch_request(self, req: JSONRPCRequest) -> None:
        """Execute registered method handler and return response."""
        handler = self._method_handlers.get(req.method)
        if not handler:
            logger.warning(f"Method not found: {req.method}")
            await self._send_raw_error(req.id, -32601, f"Method not found: '{req.method}'")
            return

        try:
            result = await handler(req.params)
            response = JSONRPCResponse(id=req.id, result=result)
            await self.send_response(response)
        except Exception as handler_err:
            logger.exception(f"Handler execution failure on {req.method}: {handler_err}")
            await self._send_raw_error(req.id, -32603, f"Execution failed: {str(handler_err)}")

    async def _dispatch_notification(self, req: JSONRPCRequest) -> None:
        """Execute notification handler without sending any response."""
        handler = self._method_handlers.get(req.method)
        if handler:
            try:
                await handler(req.params)
            except Exception as notif_err:
                logger.error(f"Notification error on {req.method}: {notif_err}")

    async def _send_raw_error(self, req_id: Any, code: int, message: str) -> None:
        """Helper to emit an error packet."""
        envelope = {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {"code": code, "message": message},
        }
        sys.stdout.write(json.dumps(envelope) + "\n")
        sys.stdout.flush()


# --- Demonstration Execution Block ---
async def handle_ping(params: Optional[Dict[str, Any]]) -> Dict[str, str]:
    return {"status": "healthy", "timestamp": "2027-01-15T12:00:00Z"}


async def main() -> None:
    multiplexer = MCPWireMultiplexer()
    multiplexer.register_handler("ping", handle_ping)
    # In production, multiplexer.start() listens on sys.stdin.


if __name__ == "__main__":
    asyncio.run(main())
