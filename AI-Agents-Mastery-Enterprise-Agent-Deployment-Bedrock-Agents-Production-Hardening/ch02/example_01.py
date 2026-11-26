import os
import sys
import json
from typing import Dict, Any, List
import vertexai
from vertexai.generative_models import (
    GenerativeModel,
    Tool,
    grounding,
    GenerationConfig,
    GenerationResponse
)

class VertexADKQuickWinAgent:
    """Production Quick-Win Google ADK Agent with Search Grounding."""

    def __init__(self, project_id: str, location: str = "us-central1"):
        self.project_id = project_id
        self.location = location
        vertexai.init(project=self.project_id, location=self.location)
        
        # Configure native Google Search Grounding tool
        self.search_tool = Tool.from_google_search_retrieval(
            grounding.GoogleSearchRetrieval()
        )
        
        self.model = GenerativeModel(
            model_name="gemini-2.5-pro",
            tools=[self.search_tool],
            system_instruction=[
                "You are an enterprise AI architect assistant for Google Cloud Platform.",
                "Always ground factual claims in verified search results.",
                "Provide precise, actionable architectural recommendations."
            ]
        )
        
        self.gen_config = GenerationConfig(
            temperature=0.2,
            top_p=0.95,
            max_output_tokens=2048
        )

    def execute_query(self, query: str) -> Dict[str, Any]:
        """Dispatches query to Gemini 2.5 with grounding and extracts citations."""
        try:
            response: GenerationResponse = self.model.generate_content(
                query,
                generation_config=self.gen_config
            )
            
            grounding_metadata = response.candidates[0].grounding_metadata
            citations = []
            
            if grounding_metadata and grounding_metadata.grounding_chunks:
                for chunk in grounding_metadata.grounding_chunks:
                    if chunk.web:
                        citations.append({
                            "title": chunk.web.title,
                            "uri": chunk.web.uri
                        })
            
            return {
                "status": "SUCCESS",
                "response_text": response.text,
                "citations_count": len(citations),
                "citations": citations,
                "search_queries": list(grounding_metadata.web_search_queries or [])
            }
        except Exception as e:
            return {"status": "ERROR", "error": str(e)}

if __name__ == "__main__":
    project = os.getenv("GOOGLE_CLOUD_PROJECT", "demo-gcp-enterprise")
    agent = VertexADKQuickWinAgent(project_id=project)
    print("Executing grounded enterprise query...")
    result = agent.execute_query(
        "What are the official network security best practices for Vertex AI private endpoints?"
    )
    print(json.dumps(result, indent=2))
