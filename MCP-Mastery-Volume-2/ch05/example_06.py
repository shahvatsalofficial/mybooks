"""
Dynamic MCP Tool Adapter for LangGraph StateGraphs
Author: Vatsal Shah | Opportunity4u Press
Runtime: Python 3.11+ with LangChain, LangGraph & MCP SDK
"""

import asyncio
import logging
from typing import List, Dict, Any, Type, Optional
from pydantic import BaseModel, create_model, Field
from langchain_core.tools import StructuredTool
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("mcp.langgraph.adapter")

class McpLangGraphAdapter:
    """Discovers MCP tools and synthesizes LangChain StructuredTool instances."""

    def __init__(self, server_params: StdioServerParameters):
        self.params = server_params
        self.session: Optional[ClientSession] = None
        self._exit_stack = None

    async def initialize(self):
        """Establish persistent connection to MCP server."""
        from contextlib import AsyncExitStack
        self._exit_stack = AsyncExitStack()
        read_stream, write_stream = await self._exit_stack.enter_async_context(
            stdio_client(self.params)
        )
        self.session = await self._exit_stack.enter_async_context(
            ClientSession(read_stream, write_stream)
        )
        await self.session.initialize()
        logger.info("Successfully initialized MCP ClientSession for LangGraph.")

    def _json_schema_to_pydantic(self, name: str, schema: Dict[str, Any]) -> Type[BaseModel]:
        """Dynamically generate a Pydantic v2 model from a JSON Schema object."""
        properties = schema.get("properties", {})
        required = set(schema.get("required", []))
        fields: Dict[str, Any] = {}

        type_mapping = {
            "string": str,
            "integer": int,
            "number": float,
            "boolean": bool,
            "array": list,
            "object": dict
        }

        for prop_name, prop_spec in properties.items():
            prop_type = type_mapping.get(prop_spec.get("type", "string"), Any)
            is_required = prop_name in required
            default_val = ... if is_required else prop_spec.get("default", None)
            doc = prop_spec.get("description", "")

            fields[prop_name] = (prop_type, Field(default=default_val, description=doc))

        return create_model(f"{name}Arguments", **fields)

    async def get_tools(self) -> List[StructuredTool]:
        """Fetch remote MCP tools and synthesize LangChain StructuredTool instances."""
        if not self.session:
            raise RuntimeError("Adapter must be initialized before fetching tools.")

        tools_list_response = await self.session.list_tools()
        synthesized_tools: List[StructuredTool] = []

        for mcp_tool in tools_list_response.tools:
            tool_name = mcp_tool.name
            description = mcp_tool.description or f"Execute {tool_name}"
            args_model = self._json_schema_to_pydantic(tool_name, mcp_tool.inputSchema)

            # Define async invocation closure
            async def make_coroutine(t_name=tool_name, **kwargs) -> str:
                logger.info(f"LangGraph dispatching call to MCP tool: {t_name} with args: {kwargs}")
                result = await self.session.call_tool(t_name, arguments=kwargs)
                # Aggregate text contents
                output_texts = [item.text for item in result.content if hasattr(item, "text")]
                return "\n".join(output_texts) if output_texts else "Execution completed."

            langchain_tool = StructuredTool(
                name=tool_name,
                description=description,
                args_schema=args_model,
                coroutine=make_coroutine
            )
            synthesized_tools.append(langchain_tool)
            logger.info(f"Synthesized LangGraph tool: {tool_name}")

        return synthesized_tools

    async def close(self):
        """Cleanly terminate MCP session and process pipes."""
        if self._exit_stack:
            await self._exit_stack.aclose()
            logger.info("MCP ClientSession closed.")
