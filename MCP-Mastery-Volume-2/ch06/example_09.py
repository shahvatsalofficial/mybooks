"""
universal_mcp_llm_gateway.py - Multi-Provider LLM Gateway for MCP
"""

from abc import ABC, abstractmethod
import asyncio
import json
import logging
from typing import Any, Dict, List, Optional
from mcp.types import Tool as MCPTool

logger = logging.getLogger("LLM-Gateway")


class BaseLLMAdapter(ABC):
    """Abstract interface for LLM provider adapters."""

    @abstractmethod
    def format_tools(self, mcp_tools: List[MCPTool]) -> Any:
        """Transpiles MCP tools into provider-specific format."""
        pass

    @abstractmethod
    async def generate_response(self, messages: List[Dict[str, Any]], tools: Any) -> Dict[str, Any]:
        """Dispatches inference request and returns normalized response dictionary."""
        pass


class OpenAIGatewayAdapter(BaseLLMAdapter):
    """Adapter for OpenAI Chat Completions API."""

    def __init__(self, api_key: str, model: str = "gpt-4o"):
        from openai import AsyncOpenAI
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model

    def format_tools(self, mcp_tools: List[MCPTool]) -> List[Dict[str, Any]]:
        formatted = []
        for t in mcp_tools:
            formatted.append({
                "type": "function",
                "function": {
                    "name": t.name,
                    "description": t.description or "",
                    "parameters": t.inputSchema or {"type": "object", "properties": {}}
                }
            })
        return formatted

    async def generate_response(self, messages: List[Dict[str, Any]], tools: Any) -> Dict[str, Any]:
        resp = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=tools or None
        )
        msg = resp.choices[0].message
        tool_calls = []
        if msg.tool_calls:
            for tc in msg.tool_calls:
                tool_calls.append({
                    "id": tc.id,
                    "name": tc.function.name,
                    "arguments": json.loads(tc.function.arguments)
                })
        return {
            "content": msg.content,
            "tool_calls": tool_calls,
            "raw_message": msg.to_dict()
        }


class AnthropicGatewayAdapter(BaseLLMAdapter):
    """Adapter for Anthropic Claude Messages API."""

    def __init__(self, api_key: str, model: str = "claude-3-5-sonnet-20241022"):
        import anthropic
        self.client = anthropic.AsyncAnthropic(api_key=api_key)
        self.model = model

    def format_tools(self, mcp_tools: List[MCPTool]) -> List[Dict[str, Any]]:
        # Anthropic uses input_schema matching MCP directly!
        return [{
            "name": t.name,
            "description": t.description or "",
            "input_schema": t.inputSchema or {"type": "object", "properties": {}}
        } for t in mcp_tools]

    async def generate_response(self, messages: List[Dict[str, Any]], tools: Any) -> Dict[str, Any]:
        # Filter system prompt
        system_prompt = next((m["content"] for m in messages if m["role"] == "system"), "")
        user_msgs = [m for m in messages if m["role"] != "system"]

        resp = await self.client.messages.create(
            model=self.model,
            system=system_prompt,
            messages=user_msgs,
            tools=tools or None,
            max_tokens=4096
        )

        tool_calls = []
        text_content = ""
        for block in resp.content:
            if block.type == "text":
                text_content += block.text
            elif block.type == "tool_use":
                tool_calls.append({
                    "id": block.id,
                    "name": block.name,
                    "arguments": block.input
                })

        return {
            "content": text_content,
            "tool_calls": tool_calls,
            "raw_message": resp
        }


class ResilientMCPGateway:
    """Multi-provider orchestrator with automatic provider fallback."""

    def __init__(self, primary: BaseLLMAdapter, secondary: BaseLLMAdapter):
        self.primary = primary
        self.secondary = secondary

    async def execute_with_fallback(self, messages: List[Dict[str, Any]], mcp_tools: List[MCPTool]) -> Dict[str, Any]:
        try:
            logger.info("Attempting inference with Primary Provider...")
            tools = self.primary.format_tools(mcp_tools)
            return await self.primary.generate_response(messages, tools)
        except Exception as e:
            logger.warning(f"Primary provider failed with error: {e}. Falling back to Secondary...")
            tools = self.secondary.format_tools(mcp_tools)
            return await self.secondary.generate_response(messages, tools)
