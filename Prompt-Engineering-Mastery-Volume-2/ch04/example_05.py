import asyncio
import json
from typing import Dict, Any, List
import subprocess

class MCPClientAdapter:
    def __init__(self, server_command: List[str]):
        self.server_command = server_command
        self.process: Optional[asyncio.subprocess.Process] = None
        self.request_id = 0

    async def connect(self):
        """Spawns MCP server subprocess communicating over stdio."""
        self.process = await asyncio.create_subprocess_exec(
            *self.server_command,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        # Perform MCP initialization handshake
        init_payload = {
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "clientInfo": {"name": "ReActEnterpriseHost", "version": "1.0.0"}
            }
        }
        await self._send_rpc(init_payload)
        response = await self._read_rpc()

    def _next_id(self) -> int:
        self.request_id += 1
        return self.request_id

    async def _send_rpc(self, payload: Dict[str, Any]):
        msg = json.dumps(payload) + "\n"
        self.process.stdin.write(msg.encode("utf-8"))
        await self.process.stdin.drain()

    async def _read_rpc(self) -> Dict[str, Any]:
        line = await self.process.stdout.readline()
        if not line:
            raise ConnectionResetError("MCP server terminated stdout stream.")
        return json.loads(line.decode("utf-8"))

    async def list_tools(self) -> List[Dict[str, Any]]:
        req = {
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": "tools/list",
            "params": {}
        }
        await self._send_rpc(req)
        res = await self._read_rpc()
        return res.get("result", {}).get("tools", [])

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        req = {
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": "tools/call",
            "params": {"name": tool_name, "arguments": arguments}
        }
        await self._send_rpc(req)
        res = await self._read_rpc()
        content_items = res.get("result", {}).get("content", [])
        text_outputs = [item["text"] for item in content_items if item.get("type") == "text"]
        return "\n".join(text_outputs) if text_outputs else json.dumps(res.get("result", {}))
