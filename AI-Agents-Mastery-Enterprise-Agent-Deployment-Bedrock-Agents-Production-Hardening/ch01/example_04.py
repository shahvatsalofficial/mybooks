import boto3
from typing import Dict, Any, List

class BedrockKnowledgeBaseRAG:
    """Production wrapper for Bedrock Knowledge Base hybrid semantic retrieval."""
    
    def __init__(self, kb_id: str, model_arn: str, region_name: str = "us-east-1"):
        self.client = boto3.client("bedrock-agent-runtime", region_name=region_name)
        self.kb_id = kb_id
        self.model_arn = model_arn

    def retrieve_and_generate(self, user_prompt: str) -> Dict[str, Any]:
        """Executes full RAG generation: queries OpenSearch Serverless and generates grounded response."""
        response = self.client.retrieve_and_generate(
            input={"text": user_prompt},
            retrieveAndGenerateConfiguration={
                "type": "KNOWLEDGE_BASE",
                "knowledgeBaseConfiguration": {
                    "knowledgeBaseId": self.kb_id,
                    "modelArn": self.model_arn,
                    "retrievalConfiguration": {
                        "vectorSearchConfiguration": {
                            "numberOfResults": 5,
                            "overrideSearchType": "HYBRID"
                        }
                    }
                }
            }
        )
        output_text = response["output"]["text"]
        citations = []
        for cite in response.get("citations", []):
            for ref in cite.get("retrievedReferences", []):
                citations.append({
                    "source_uri": ref.get("location", {}).get("s3Location", {}).get("uri", "unknown"),
                    "snippet": ref.get("content", {}).get("text", "")[:120]
                })
        return {"answer": output_text, "citations": citations}

if __name__ == "__main__":
    print("-> Bedrock Knowledge Base RAG Engine Initialized (Hybrid OpenSearch Mode Active)")
