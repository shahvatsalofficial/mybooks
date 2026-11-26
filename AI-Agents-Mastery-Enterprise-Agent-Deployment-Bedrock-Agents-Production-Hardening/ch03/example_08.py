import time
from typing import Dict, Any
from azure.cosmos import CosmosClient, PartitionKey

class CosmosDBSessionMirror:
    """Mirrors Azure AI Agent thread messages to Azure Cosmos DB NoSQL container."""

    def __init__(self, endpoint: str, key: str, database_name: str = "AgentAuditDB"):
        self.client = CosmosClient(endpoint, credential=key)
        self.db = self.client.create_database_if_not_exists(id=database_name)
        self.container = self.db.create_container_if_not_exists(
            id="ThreadAudits",
            partition_key=PartitionKey(path="/tenant_id"),
            offer_throughput=400
        )

    def record_turn(self, tenant_id: str, thread_id: str, turn_index: int, role: str, content: str) -> None:
        doc = {
            "id": f"{thread_id}_{turn_index}",
            "tenant_id": tenant_id,
            "thread_id": thread_id,
            "turn_index": turn_index,
            "role": role,
            "content": content,
            "logged_at": int(time.time())
        }
        self.container.upsert_item(doc)
        print(f"Mirrored turn {turn_index} of thread {thread_id} to Cosmos DB.")

if __name__ == "__main__":
    print("CosmosDBSessionMirror initialized successfully.")
