"""
streaming_openai_agent.py - Asynchronous Streaming Agent with MCP Execution
"""

import asyncio
import json
import logging
from typing import Any, Dict, List
from openai import AsyncOpenAI

from mcp import StdioServerParameters
from mcp_openai_bridge import AutonomousMCPClient, MCPOpenAITranspiler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("OpenAI-Agent")


class OpenAIMCPAgent:
    """Coordinates conversational reasoning and concurrent MCP tool execution."""

    def __init__(self, openai_client: AsyncOpenAI, mcp_client: AutonomousMCPClient, model: str = "gpt-4o"):
        self.openai = openai_client
        self.mcp = mcp_client
        self.model = model
        self.messages: List[Dict[str, Any]] = [
            {"role": "system", "content": "You are an autonomous engineering assistant equipped with enterprise tools."}
        ]

    async def run_turn(self, user_prompt: str) -> str:
        """Executes a complete reasoning turn, handling parallel tool dispatches."""
        self.messages.append({"role": "user", "content": user_prompt})

        # Discover tools from MCP
        tools = await self.mcp.start()

        while True:
            # Dispatch Chat Completion with available tools
            response = await self.openai.chat.completions.create(
                model=self.model,
                messages=self.messages,
                tools=tools,
                tool_choice="auto"
            )

            choice = response.choices[0]
            message = choice.message

            # Case A: Model issued tool calls
            if message.tool_calls:
                # 1. Append assistant call to context
                self.messages.append(message.to_dict())

                # 2. Concurrently execute all tool calls
                async def dispatch_single(tc):
                    call_id = tc.id
                    func_name = tc.function.name
                    args = json.loads(tc.function.arguments)
                    try:
                        res_text = await self.mcp.execute_tool(func_name, args)
                    except Exception as e:
                        res_text = json.dumps({"error": str(e), "status": "failure"})
                    
                    return {
                        "role": "tool",
                        "tool_call_id": call_id,
                        "content": res_text
                    }

                tasks = [dispatch_single(tc) for tc in message.tool_calls]
                tool_results = await asyncio.gather(*tasks)

                # 3. Append tool responses to message context
                for tr in tool_results:
                    self.messages.append(tr)

                # Re-loop to allow model to synthesize tool outputs
                continue

            # Case B: Model returned natural language answer
            final_content = message.content or ""
            self.messages.append({"role": "assistant", "content": final_content})
            return final_content


async def main():
    # Configure MCP Server Subprocess (e.g., PostgreSQL or Node tool)
    server_params = StdioServerParameters(
        command="node",
        args=["enterprise_analytics_mcp.js"],
        env={"NODE_ENV": "production"}
    )

    mcp_client = AutonomousMCPClient(server_params)
    openai_client = AsyncOpenAI()

    agent = OpenAIMCPAgent(openai_client, mcp_client, model="gpt-4o")

    try:
        query = "What were our top 3 enterprise churn reasons in Q3?"
        print(f"\n[USER]: {query}\n")
        answer = await agent.run_turn(query)
        print(f"\n[ASSISTANT]: {answer}\n")
    finally:
        await mcp_client.close()

if __name__ == "__main__":
    asyncio.run(main())
