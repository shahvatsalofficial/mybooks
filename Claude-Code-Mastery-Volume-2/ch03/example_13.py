#!/usr/bin/env python3
"""
Enterprise Local Semantic Embeddings MCP Server
Language: Python 3.11+
Runs local all-MiniLM-L6-v2 embeddings on CPU with FAISS index search
"""

from mcp.server.fastmcp import FastMCP, Context
from pydantic import BaseModel, Field
import numpy as np
import asyncio

mcp = FastMCP("Enterprise-Vector-Intel")

# Global in-memory index state (initialized lazily)
model = None
documents = []
embeddings_matrix = None

def init_model():
    global model
    if model is None:
        from sentence_transformers import SentenceTransformer
        # Lightweight 80MB model, runs in 15ms on standard CPU
        model = SentenceTransformer("all-MiniLM-L6-v2")

class IndexDocumentInput(BaseModel):
    document_id: str = Field(..., description="Unique document or function identifier")
    text_content: str = Field(..., description="Raw source code or architectural documentation snippet")

@mcp.tool()
async def index_document(input_data: IndexDocumentInput, ctx: Context) -> str:
    """Embeds and indexes a code or architectural documentation snippet into the local vector space."""
    global documents, embeddings_matrix
    init_model()
    
    ctx.info(f"Computing local vector embedding for: {input_data.document_id}...")
    
    # Offload CPU embedding calculation to worker thread to prevent GIL event loop block!
    embedding = await asyncio.to_thread(model.encode, input_data.text_content)
    
    documents.append({"id": input_data.document_id, "text": input_data.text_content})
    if embeddings_matrix is None:
        embeddings_matrix = np.array([embedding])
    else:
        embeddings_matrix = np.vstack([embeddings_matrix, embedding])
        
    return f"Successfully indexed '{input_data.document_id}' (Total indexed: {len(documents)})."

class SearchInput(BaseModel):
    query: str = Field(..., description="Natural language semantic search query")
    top_k: int = Field(default=3, ge=1, le=10, description="Number of top semantic matches to return")

@mcp.tool()
async def semantic_code_search(input_data: SearchInput, ctx: Context) -> str:
    """Executes semantic cosine-similarity search over indexed enterprise codebases."""
    global documents, embeddings_matrix
    if embeddings_matrix is None or len(documents) == 0:
        return "ERROR: Vector index is empty. Please index documents before querying."
        
    init_model()
    ctx.info(f"Executing semantic search for query: '{input_data.query}'")
    
    query_vec = await asyncio.to_thread(model.encode, input_data.query)
    
    # Compute cosine similarities in parallel numpy vector arithmetic
    norms = np.linalg.norm(embeddings_matrix, axis=1) * np.linalg.norm(query_vec)
    similarities = np.dot(embeddings_matrix, query_vec) / (norms + 1e-9)
    
    top_indices = np.argsort(similarities)[::-1][:input_data.top_k]
    
    results = []
    for rank, idx in enumerate(top_indices):
        score = float(similarities[idx])
        doc = documents[idx]
        results.append(f"**Match #{rank + 1}** (Score: {score:.4f}) — [{doc['id']}]:\n{doc['text'][:250]}...\n")
        
    return f"### Semantic Search Results for '{input_data.query}':\n\n" + "\n".join(results)

if __name__ == "__main__":
    mcp.run(transport="stdio")
