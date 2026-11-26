"""
Recipe 02.2: Bedrock Knowledge Base Hybrid Retrieval with Metadata Filtering.
Author: Vatsal Shah (Lead Enterprise AI Architect)
Architecture: Claude AI Mastery Series — Volume 3
"""

import boto3
import logging
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from botocore.config import Config

logger = logging.getLogger("BedrockKBRetrieval")
logger.setLevel(logging.INFO)


class RetrievedPassage(BaseModel):
    content_text: str
    source_uri: str
    relevance_score: float
    chunk_id: str
    metadata: Dict[str, Any]


class BedrockKnowledgeBaseClient:
    """Production client for querying Amazon Bedrock Knowledge Bases backed by OpenSearch Serverless."""

    def __init__(self, knowledge_base_id: str, region_name: str = "us-east-1"):
        self.knowledge_base_id = knowledge_base_id
        self.region_name = region_name

        config = Config(
            region_name=self.region_name,
            retries={"max_attempts": 3, "mode": "adaptive"},
            connect_timeout=3,
            read_timeout=15,
        )

        self.client = boto3.client("bedrock-agent-runtime", config=config)
        logger.info(f"Initialized Bedrock KB Client for ID: {self.knowledge_base_id}")

    def query_knowledge_base(
        self,
        query: str,
        number_of_results: int = 5,
        department_filter: Optional[str] = None
    ) -> List[RetrievedPassage]:
        """
        Executes hybrid vector + lexical search with optional metadata attribute filtering.
        """
        retrieval_config: Dict[str, Any] = {
            "vectorSearchConfiguration": {
                "numberOfResults": number_of_results,
                "overrideSearchType": "HYBRID",  # Enforce dense k-NN + sparse BM25 fusion
            }
        }

        # Apply strict metadata filtering to prevent cross-department data leakage
        if department_filter:
            retrieval_config["vectorSearchConfiguration"]["filter"] = {
                "equals": {
                    "key": "department",
                    "value": department_filter
                }
            }

        try:
            logger.info(f"Querying KB [{self.knowledge_base_id}] with query: '{query}'")
            response = self.client.retrieve(
                knowledgeBaseId=self.knowledge_base_id,
                retrievalQuery={"text": query},
                retrievalConfiguration=retrieval_config
            )

            raw_results = response.get("retrievalResults", [])
            passages: List[RetrievedPassage] = []

            for r in raw_results:
                content = r.get("content", {}).get("text", "")
                location = r.get("location", {}).get("s3Location", {}).get("uri", "unknown")
                score = r.get("score", 0.0)
                metadata = r.get("metadata", {})
                chunk_id = metadata.get("x-amz-bedrock-kb-chunk-id", "unknown")

                passages.append(
                    RetrievedPassage(
                        content_text=content,
                        source_uri=location,
                        relevance_score=round(score, 4),
                        chunk_id=chunk_id,
                        metadata=metadata
                    )
                )

            logger.info(f"Successfully retrieved {len(passages)} passages from Knowledge Base.")
            return passages

        except Exception as e:
            logger.error(f"Failed to retrieve from Bedrock Knowledge Base: {str(e)}")
            raise RuntimeError(f"Knowledge Base retrieval failed: {str(e)}") from e
