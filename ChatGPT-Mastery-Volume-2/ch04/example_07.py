# CATASTROPHIC MIGRATION BUG
# Updated query generation to new model:
query_embedding = client.embeddings.create(model="text-embedding-3-large", input=query, dimensions=1536)
# But left the 2.5 million database records embedded with ada-002!
