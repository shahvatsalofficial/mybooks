"""
Production Enterprise Financial Assistant Implementation
Demonstrates complete Assistants API v2 lifecycle with Code Interpreter, File Search, and Streaming.
Author: Vatsal Shah, Enterprise AI Architect
"""
import os
import json
import asyncio
import logging
from typing import Dict, Any, List
from openai import AsyncOpenAI
from pydantic import BaseModel, Field

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("AssistantsOrchestrator")

# 1. Custom Function Calling Tool Schemas
class AccountBalanceArgs(BaseModel):
    account_number: str = Field(description="Institutional account identifier, e.g., ACC-1002")

def execute_balance_query(account_number: str) -> Dict[str, Any]:
    return {
        "account_number": account_number,
        "cash_balance_usd": 1250000.00,
        "credit_facility_available": 5000000.00,
        "status": "CLEAR"
    }

class EnterpriseAssistantManager:
    def __init__(self, api_key: str = None):
        self.client = AsyncOpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))
        self.assistant = None

    async def initialize_assistant(self) -> str:
        """Provisions or updates the persistent Assistant entity."""
        logger.info("Provisioning Enterprise Financial Assistant...")
        self.assistant = await self.client.beta.assistants.create(
            name="Institutional Financial Analyst",
            instructions=(
                "You are an expert quantitative financial analyst for an institutional asset manager. "
                "You have access to a sandboxed Code Interpreter to run statistical models, calculate VaR, "
                "and plot visualizations, as well as tools to check live account balances. "
                "Always verify mathematical calculations using Python."
            ),
            model="gpt-4o",
            tools=[
                {"type": "code_interpreter"},
                {
                    "type": "function",
                    "function": {
                        "name": "verify_account_balance",
                        "description": "Check current liquid cash and credit facility balances for an account.",
                        "parameters": AccountBalanceArgs.model_json_schema(),
                        "strict": True
                    }
                }
            ]
        )
        logger.info(f"Assistant provisioned with ID: {self.assistant.id}")
        return self.assistant.id

    async def execute_interactive_turn(self, thread_id: str, user_prompt: str) -> None:
        """Submits a message to the thread and executes an event-driven streaming Run."""
        # Step 1: Append User Message to Thread
        await self.client.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=user_prompt
        )

        # Step 2: Launch Streaming Run
        logger.info(f"Initiating Run on Thread: {thread_id}...")
        async with self.client.beta.threads.runs.stream(
            thread_id=thread_id,
            assistant_id=self.assistant.id,
            max_prompt_tokens=10000,
            max_completion_tokens=2000
        ) as stream:
            async for event in stream:
                # Handle streaming text tokens
                if event.event == "thread.message.delta":
                    delta_content = event.data.delta.content
                    if delta_content and len(delta_content) > 0:
                        text_val = delta_content[0].text.value
                        print(text_val, end="", flush=True)

                # Handle tool execution requirements
                elif event.event == "thread.run.requires_action":
                    print("

[Action Required: Dispatching External Tool Handlers...]")
                    run_obj = event.data
                    tool_outputs = []
                    
                    for tc in run_obj.required_action.submit_tool_outputs.tool_calls:
                        if tc.function.name == "verify_account_balance":
                            args = json.loads(tc.function.arguments)
                            res = execute_balance_query(args["account_number"])
                            tool_outputs.append({
                                "tool_call_id": tc.id,
                                "output": json.dumps(res)
                            })

                    # Submit tool outputs and resume the stream
                    async with self.client.beta.threads.runs.submit_tool_outputs_stream(
                        thread_id=thread_id,
                        run_id=run_obj.id,
                        tool_outputs=tool_outputs
                    ) as resumed_stream:
                        async for resumed_event in resumed_stream:
                            if resumed_event.event == "thread.message.delta":
                                delta = resumed_event.data.delta.content
                                if delta and len(delta) > 0:
                                    print(delta[0].text.value, end="", flush=True)

        print("

--- Turn Complete ---")

async def main():
    manager = EnterpriseAssistantManager()
    await manager.initialize_assistant()
    
    # Create persistent thread
    thread = await manager.client.beta.threads.create()
    logger.info(f"Created persistent thread: {thread.id}")

    # Prompt requiring Code Interpreter + Function Calling
    test_query = (
        "Check the balance for account ACC-1002. Then, write and execute a Python script "
        "to calculate the compound growth of that cash balance over 5 years at a 4.5% annual yield."
    )
    print(f"
User Query: {test_query}
")
    await manager.execute_interactive_turn(thread.id, test_query)

if __name__ == "__main__":
    asyncio.run(main())
