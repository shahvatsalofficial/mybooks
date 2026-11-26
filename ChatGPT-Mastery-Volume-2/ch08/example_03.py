"""
Production Semantic Caching API Gateway
Intercepts redundant queries using cosine vector similarity in Redis.
Author: Vatsal Shah, Enterprise AI Architect
"""
import numpy as np
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from openai import OpenAI

app = FastAPI(title="Enterprise Semantic Gateway")
client = OpenAI()

class PromptRequest(BaseModel):
    prompt: str
    temperature: float = 0.7

# In-memory vector cache simulation (Production uses Redis RediSearch)
cache_store = [] # List of tuples: (embedding_vector, completion_text)

def get_embedding(text: str) -> np.ndarray:
    resp = client.embeddings.create(model="text-embedding-3-small", input=text)
    vec = np.array(resp.data[0].embedding, dtype=np.float32)
    return vec / np.linalg.norm(vec) # Normalize for fast dot product

@app.post("/v1/chat/completions/cached")
async def cached_completion(req: PromptRequest):
    query_vec = get_embedding(req.prompt)

    # 1. Search Semantic Cache
    for cached_vec, cached_text in cache_store:
        similarity = float(np.dot(query_vec, cached_vec))
        if similarity >= 0.96:
            return {
                "source": "semantic_cache",
                "similarity_score": round(similarity, 4),
                "completion": cached_text
            }

    # 2. Cache Miss: Dispatch to OpenAI
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": req.prompt}],
            temperature=req.temperature
        )
        completion_text = response.choices[0].message.content
        
        # 3. Store in cache
        cache_store.append((query_vec, completion_text))
        
        return {
            "source": "openai_api",
            "completion": completion_text
        }
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))
