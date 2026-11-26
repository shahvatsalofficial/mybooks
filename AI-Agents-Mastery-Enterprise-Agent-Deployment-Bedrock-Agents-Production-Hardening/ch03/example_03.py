from typing import Dict, Any, List
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import AzureAISearchTool

class AzureAISearchGroundingManager:
    """Connects Azure AI Agents to Azure AI Search hybrid vector indices."""

    @staticmethod
    def create_search_tool(index_name: str, search_endpoint: str) -> AzureAISearchTool:
        """Constructs an Azure AI Search tool attachment with semantic reranking."""
        return AzureAISearchTool(
            index_connection_id="/subscriptions/000-000/resourceGroups/ai-rg/providers/Microsoft.Search/searchServices/corp-search",
            index_name=index_name,
            query_type="vector_semantic_hybrid",
            semantic_configuration_name="enterprise-reranker-v1"
        )

    @staticmethod
    def build_grounded_agent(client: AIProjectClient, search_tool: AzureAISearchTool) -> str:
        """Creates an agent armed with corporate search capabilities."""
        agent = client.agents.create_agent(
            model="gpt-4o",
            name="it-support-grounded-agent",
            instructions=(
                "You are an enterprise IT operations assistant. "
                "Always query the corporate search index before formulating responses. "
                "Cite document titles and internal knowledge base IDs."
            ),
            tools=search_tool.definitions
        )
        return agent.id

if __name__ == "__main__":
    print("AzureAISearchGroundingManager loaded.")
