import os
import time
import json
from typing import Dict, Any
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import CodeInterpreterTool

class AzureAgentQuickWin:
    """Production Quick-Win client for Azure AI Agent Service."""

    def __init__(self, endpoint: str, project_name: str):
        self.credential = DefaultAzureCredential()
        self.project_client = AIProjectClient(
            endpoint=endpoint,
            credential=self.credential,
            project_name=project_name
        )

    def run_statistical_analysis(self, prompt: str) -> Dict[str, Any]:
        """Creates an ephemeral agent, executes Code Interpreter, and retrieves output."""
        try:
            # 1. Initialize Code Interpreter tool
            code_tool = CodeInterpreterTool()
            
            # 2. Create the Agent in Azure AI Foundry
            agent = self.project_client.agents.create_agent(
                model="gpt-4o",
                name="enterprise-analytics-agent",
                instructions="You are an enterprise data scientist. Write and execute Python to solve analytical queries.",
                tools=code_tool.definitions
            )
            
            # 3. Create a managed Thread
            thread = self.project_client.agents.create_thread()
            
            # 4. Post User Query
            self.project_client.agents.create_message(
                thread_id=thread.id,
                role="user",
                content=prompt
            )
            
            # 5. Execute Run and Poll to Completion
            run = self.project_client.agents.create_and_process_run(
                thread_id=thread.id,
                assistant_id=agent.id
            )
            
            # 6. Fetch Generated Messages
            messages = self.project_client.agents.list_messages(thread_id=thread.id)
            latest_response = messages["data"][0]["content"][0]["text"]["value"]
            
            # 7. Cleanup ephemeral agent
            self.project_client.agents.delete_agent(agent.id)
            
            return {
                "status": "SUCCESS",
                "thread_id": thread.id,
                "run_status": run.status,
                "response": latest_response
            }
        except Exception as e:
            return {"status": "ERROR", "error": str(e)}

if __name__ == "__main__":
    endpoint = os.getenv("AZURE_AI_FOUNDRY_ENDPOINT", "https://eastus2.api.azureml.ms")
    project = os.getenv("AZURE_AI_PROJECT_NAME", "finops-analytics-prod")
    
    client = AzureAgentQuickWin(endpoint, project)
    print("Executing Azure AI Agent with sandboxed Code Interpreter...")
    result = client.run_statistical_analysis(
        "Calculate the 99th percentile and mean latency for these response times: [12, 14, 18, 22, 19, 450, 15, 13, 16]."
    )
    print(json.dumps(result, indent=2))
