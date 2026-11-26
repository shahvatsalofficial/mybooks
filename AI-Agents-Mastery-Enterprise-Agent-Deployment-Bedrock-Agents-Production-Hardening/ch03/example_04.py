import json
from typing import Dict, Any, List
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import ToolOutput

class ClientSideToolHandler:
    """Fulfills external tool requests emitted by Azure AI Agent Service."""

    def __init__(self, client: AIProjectClient):
        self.client = client

    def process_tool_calls(self, thread_id: str, run_id: str, required_action: Any) -> None:
        """Parses tool calls, executes local functions, and submits tool outputs back to Azure."""
        tool_outputs: List[ToolOutput] = []
        
        for tool_call in required_action.submit_tool_outputs.tool_calls:
            call_id = tool_call.id
            fn_name = tool_call.function.name
            args = json.loads(tool_call.function.arguments)
            
            print(f"Executing function '{fn_name}' with arguments: {args}")
            
            if fn_name == "query_sap_inventory":
                observation = {"sku": args.get("sku"), "available_stock": 1420, "warehouse": "Chicago-Central"}
            elif fn_name == "create_service_ticket":
                observation = {"ticket_id": "INC-99042", "severity": args.get("severity", "P3"), "status": "ASSIGNED"}
            else:
                observation = {"error": f"Unknown tool: {fn_name}"}
                
            tool_outputs.append(
                ToolOutput(
                    tool_call_id=call_id,
                    output=json.dumps(observation)
                )
            )
            
        # Submit outputs to resume run execution
        self.client.agents.submit_tool_outputs_to_run(
            thread_id=thread_id,
            run_id=run_id,
            tool_outputs=tool_outputs
        )
        print(f"Submitted {len(tool_outputs)} tool outputs back to thread run {run_id}.")

if __name__ == "__main__":
    print("ClientSideToolHandler compiled successfully.")
