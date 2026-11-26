import asyncio
import time
from typing import Dict, Any, List, Optional
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient

class AzureThreadRunCoordinator:
    """Coordinates server-side threads and asynchronous run state polling."""

    def __init__(self, client: AIProjectClient, agent_id: str):
        self.client = client
        self.agent_id = agent_id

    async def execute_turn_async(self, thread_id: str, user_content: str, timeout_seconds: int = 120) -> Dict[str, Any]:
        """Dispatches user message and polls run state asynchronously."""
        # Append message to thread
        self.client.agents.create_message(
            thread_id=thread_id,
            role="user",
            content=user_content
        )
        
        # Initiate Run
        run = self.client.agents.create_run(
            thread_id=thread_id,
            assistant_id=self.agent_id
        )
        
        start_time = time.time()
        backoff = 0.5
        
        while time.time() - start_time < timeout_seconds:
            run_status = self.client.agents.get_run(thread_id=thread_id, run_id=run.id)
            
            if run_status.status == "completed":
                messages = self.client.agents.list_messages(thread_id=thread_id)
                assistant_msg = messages["data"][0]["content"][0]["text"]["value"]
                return {
                    "status": "COMPLETED",
                    "duration_seconds": round(time.time() - start_time, 2),
                    "response": assistant_msg
                }
            elif run_status.status == "requires_action":
                return {
                    "status": "REQUIRES_ACTION",
                    "run_id": run.id,
                    "required_action": run_status.required_action
                }
            elif run_status.status in ["failed", "cancelled", "expired"]:
                return {
                    "status": "FAILED",
                    "error": run_status.last_error
                }
            
            await asyncio.sleep(backoff)
            backoff = min(backoff * 1.5, 4.0)
            
        return {"status": "TIMEOUT", "error": "Run polling exceeded maximum timeout."}

if __name__ == "__main__":
    print("AzureThreadRunCoordinator compiled successfully.")
