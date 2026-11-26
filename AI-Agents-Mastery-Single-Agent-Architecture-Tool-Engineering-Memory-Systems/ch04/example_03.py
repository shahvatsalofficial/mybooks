import chromadb
from chromadb.config import Settings
import uuid

class EpisodicMemoryStore:
    def __init__(self, persist_dir: Optional[str] = None):
        if persist_dir:
            self.client = chromadb.PersistentClient(path=persist_dir)
        else:
            self.client = chromadb.Client(Settings(anonymized_telemetry=False))
        
        # Initialize or fetch the episodic collection
        self.collection = self.client.get_or_create_collection(
            name="agent_episodic_vault",
            metadata={"hnsw:space": "cosine"}
        )

    def record_episode(self, tenant_id: str, episode_text: str, tags: List[str]):
        doc_id = str(uuid.uuid4())
        self.collection.add(
            ids=[doc_id],
            documents=[episode_text],
            metadatas=[{
                "tenant_id": tenant_id,
                "tags": ",".join(tags),
                "timestamp": time.time()
            }]
        )
        return doc_id

    def recall_episodes(self, tenant_id: str, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        # Enforce strict multi-tenant metadata filtering
        results = self.collection.query(
            query_texts=[query],
            n_results=top_k,
            where={"tenant_id": tenant_id}
        )
        
        recalled = []
        if results and results["documents"]:
            docs = results["documents"][0]
            metas = results["metadatas"][0] if results["metadatas"] else []
            distances = results["distances"][0] if results["distances"] else []
            
            for doc, meta, dist in zip(docs, metas, distances):
                recalled.append({
                    "content": doc,
                    "metadata": meta,
                    "similarity_score": round(1.0 - dist, 4)
                })
        return recalled

# Verification
vault = EpisodicMemoryStore()
vault.record_episode(
    tenant_id="tenant_acme",
    episode_text="Customer requested custom invoice routing to accounting@acme.corp on NET-60 terms.",
    tags=["billing", "preferences"]
)
vault.record_episode(
    tenant_id="tenant_globex",
    episode_text="Globex Corporation requires all API requests to use mTLS certificates.",
    tags=["security", "infra"]
)

# Acme search must NOT see Globex memories
acme_results = vault.recall_episodes(tenant_id="tenant_acme", query="What are the billing preferences?")
print(f"Acme Recalled Count: {len(acme_results)}")
print(f"Acme Top Result: {acme_results[0]['content']}")
