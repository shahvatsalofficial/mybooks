import os
import numpy as np
from openai import OpenAI
from sklearn.metrics.pairwise import cosine_similarity

client = OpenAI()

def simulate_rag_retrieval(document_chunks: list, test_queries: list):
    # 1. Batch embed all document chunks
    chunk_res = client.embeddings.create(
        model="text-embedding-3-small",
        input=document_chunks
    )
    chunk_vectors = np.array([d.embedding for d in chunk_res.data])

    # 2. Batch embed test queries
    query_res = client.embeddings.create(
        model="text-embedding-3-small",
        input=test_queries
    )
    query_vectors = np.array([d.embedding for d in query_res.data])

    # 3. Compute cosine similarity matrix
    similarity_matrix = cosine_similarity(query_vectors, chunk_vectors)

    # 4. Evaluate top-3 recall
    for i, q in enumerate(test_queries):
        top_3_indices = np.argsort(similarity_matrix[i])[::-1][:3]
        top_scores = similarity_matrix[i][top_3_indices]
        print(f"\nQuery: '{q}'")
        for rank, (idx, score) in enumerate(zip(top_3_indices, top_scores)):
            print(f"  Rank {rank+1} (Score: {score:.4f}): Chunk #{idx} -> '{document_chunks[idx][:80]}...'")

# Test Harness
chunks = [
    "Section 1: Enterprise Password Requirements. Minimum 16 characters with MFA enabled.",
    "Section 2: Remote Work Security. VPN mandatory when accessing internal code repositories.",
    "Section 3: Device Encryption. All laptops must enforce FileVault or BitLocker 256-bit AES."
]
queries = [
    "How long does my laptop password need to be?",
    "Do I need to connect to VPN from home to push code?"
]
simulate_rag_retrieval(chunks, queries)
