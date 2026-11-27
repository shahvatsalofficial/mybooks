"""
Recipe 02.1: Resilient Parallel Tool Dispatcher in Python
Author: Vatsal Shah (Vatsal Shah)
License: Apache-2.0
"""

import os
import sys
import json
import time
import asyncio
import logging
from typing import List, Dict, Any, Callable, Coroutine, Optional
import httpx
from pydantic import BaseModel, Field

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("ToolDispatcher")

# --- Domain Models & Tool Schemas ---
class DatabaseQueryInput(BaseModel):
    table: str = Field(..., description="Target database table name", enum=["users", "orders", "inventory"])
    filter_id: int = Field(..., description="Unique entity primary key", ge=1)

class NetworkPingInput(BaseModel):
    host: str = Field(..., description="Target hostname or IP address")
    port: int = Field(..., description="Target port number", ge=1, le=65535)

# Tool Definition Registry for Claude
TOOL_DEFINITIONS = [
    {
        "name": "query_database_record",
        "description": "Fetches a single verified record from the enterprise SQL cluster.",
        "input_schema": {
            "type": "object",
            "properties": {
                "table": {"type": "string", "enum": ["users", "orders", "inventory"]},
                "filter_id": {"type": "integer", "minimum": 1}
            },
            "required": ["table", "filter_id"]
        }
    },
    {
        "name": "check_service_health",
        "description": "Executes a synthetic network ping against an internal microservice.",
        "input_schema": {
            "type": "object",
            "properties": {
                "host": {"type": "string"},
                "port": {"type": "integer", "minimum": 1, "maximum": 65535}
            },
            "required": ["host", "port"]
        }
    }
]

# --- Concrete Tool Handlers ---
async def handle_database_query(args: Dict[str, Any]) -> str:
    parsed = DatabaseQueryInput(**args)
    # Simulate database query latency
    await asyncio.sleep(0.15)
    records = {
        "users": {"id": parsed.filter_id, "name": "Vatsal Shah", "tier": "Enterprise"},
        "orders": {"id": parsed.filter_id, "sku": "GPU-H100-80GB", "status": "SHIPPED"},
        "inventory": {"id": parsed.filter_id, "stock": 42, "warehouse": "us-east-1a"}
    }
    return json.dumps(records.get(parsed.table, {"error": "Record not found"}))

async def handle_service_health(args: Dict[str, Any]) -> str:
    parsed = NetworkPingInput(**args)
    await asyncio.sleep(0.08)
    return json.dumps({"host": parsed.host, "port": parsed.port, "status": "HEALTHY", "latency_ms": 12.4})

TOOL_HANDLERS: Dict[str, Callable[[Dict[str, Any]], Coroutine[Any, Any, str]]] = {
    "query_database_record": handle_database_query,
    "check_service_health": handle_service_health
}

# --- Dispatcher Engine ---
class AutonomousToolOrchestrator:
    def __init__(self, api_key: Optional[str] = None, max_parallel_concurrency: int = 5):
        self.api_key = api_key or os.environ["ANTHROPIC_API_KEY"]
        self.semaphore = asyncio.Semaphore(max_parallel_concurrency)
        self.http_client = httpx.AsyncClient(timeout=60.0)

    async def _execute_single_tool(self, tool_use_block: Dict[str, Any]) -> Dict[str, Any]:
        tool_id = tool_use_block["id"]
        name = tool_use_block["name"]
        raw_args = tool_use_block.get("input", {})

        handler = TOOL_HANDLERS.get(name)
        if not handler:
            logger.error(f"Unknown tool invoked: {name}")
            return {
                "type": "tool_result",
                "tool_use_id": tool_id,
                "content": f"Execution Error: Unknown tool '{name}'. Valid tools: {list(TOOL_HANDLERS.keys())}",
                "is_error": True
            }

        async with self.semaphore:
            try:
                # Enforce strict 4-second timeout per tool execution
                result_str = await asyncio.wait_for(handler(raw_args), timeout=4.0)
                return {
                    "type": "tool_result",
                    "tool_use_id": tool_id,
                    "content": result_str,
                    "is_error": False
                }
            except asyncio.TimeoutError:
                return {
                    "type": "tool_result",
                    "tool_use_id": tool_id,
                    "content": f"Execution Error: Tool '{name}' timed out after 4.0 seconds.",
                    "is_error": True
                }
            except Exception as exc:
                return {
                    "type": "tool_result",
                    "tool_use_id": tool_id,
                    "content": f"Execution Error: {type(exc).__name__}: {str(exc)}",
                    "is_error": True
                }

    async def run_agent_turn(self, prompt: str, max_iterations: int = 5) -> str:
        messages = [{"role": "user", "content": prompt}]
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }

        for iteration in range(max_iterations):
            payload = {
                "model": "claude-3-5-sonnet-20241022",
                "max_tokens": 4096,
                "tools": TOOL_DEFINITIONS,
                "messages": messages
            }

            resp = await self.http_client.post("https://api.anthropic.com/v1/messages", headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()

            # Append the assistant's turn
            messages.append({"role": "assistant", "content": data["content"]})

            # Check if execution finished
            if data["stop_reason"] != "tool_use":
                text_blocks = [b["text"] for b in data["content"] if b.get("type") == "text"]
                return "\n".join(text_blocks)

            # Extract all tool calls
            tool_calls = [b for b in data["content"] if b.get("type") == "tool_use"]
            logger.info(f"Iteration {iteration+1}: Executing {len(tool_calls)} tool calls in parallel...")

            # Bounded parallel dispatch
            tasks = [self._execute_single_tool(tc) for tc in tool_calls]
            tool_results = await asyncio.gather(*tasks)

            # Ingest results under user role to maintain strict alternating symmetry
            messages.append({"role": "user", "content": tool_results})

        raise RuntimeError(f"Agent loop exceeded maximum iterations ({max_iterations}) without final answer.")
