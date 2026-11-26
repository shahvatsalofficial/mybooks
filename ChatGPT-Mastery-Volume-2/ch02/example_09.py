"""
Dynamic Semantic Tool Registry for Enterprise Agent Architectures
Scales tool support to hundreds of microservices with minimal token footprint.
"""
import numpy as np
from typing import List, Dict, Any, Callable
from openai import OpenAI
import json

class VectorToolRegistry:
    def __init__(self, openai_client: OpenAI):
        self.client = openai_client
        self.tools_catalog: Dict[str, Dict[str, Any]] = {}
        self.tool_handlers: Dict[str, Callable] = {}
        self.tool_embeddings: Dict[str, np.ndarray] = {}

    def register_tool(self, name: str, description: str, parameters: Dict[str, Any], handler: Callable):
        tool_definition = {
            "type": "function",
            "function": {
                "name": name,
                "description": description,
                "parameters": parameters,
                "strict": True
            }
        }
        self.tools_catalog[name] = tool_definition
        self.tool_handlers[name] = handler
        
        # Pre-compute semantic embedding of tool intent
        embed_text = f"Tool: {name}. Description: {description}"
        resp = self.client.embeddings.create(
            model="text-embedding-3-small",
            input=embed_text
        )
        embedding_vec = np.array(resp.data[0].embedding, dtype=np.float32)
        # Normalize for rapid cosine dot-product
        self.tool_embeddings[name] = embedding_vec / np.linalg.norm(embedding_vec)

    def retrieve_relevant_tools(self, user_query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        # Compute user query embedding
        resp = self.client.embeddings.create(
            model="text-embedding-3-small",
            input=user_query
        )
        query_vec = np.array(resp.data[0].embedding, dtype=np.float32)
        query_vec = query_vec / np.linalg.norm(query_vec)

        # Compute dot-product cosine similarity across all catalog tools
        scores = []
        for name, tool_vec in self.tool_embeddings.items():
            similarity = float(np.dot(query_vec, tool_vec))
            scores.append((similarity, name))

        # Rank descending
        scores.sort(key=lambda x: x[0], reverse=True)
        top_tool_names = [name for _, name in scores[:top_k]]
        
        return [self.tools_catalog[name] for name in top_tool_names]
