# fair_share_scheduler.py
import asyncio
from typing import Dict, List

class TenantQueue:
    def __init__(self, tenant_id: str, quantum_tokens: int):
        self.tenant_id = tenant_id
        self.quantum = quantum_tokens
        self.deficit = 0
        self.queue: asyncio.Queue = asyncio.Queue()

class HierarchicalScheduler:
    def __init__(self, total_capacity_tpm: int = 150000):
        self.total_capacity = total_capacity_tpm
        self.tenants: Dict[str, TenantQueue] = {}

    def register_tenant(self, tenant_id: str, weight: float):
        # Quantum proportional to allocated financial weight
        quantum = int(weight * 5000)
        self.tenants[tenant_id] = TenantQueue(tenant_id, quantum)

    async def enqueue_request(self, tenant_id: str, request_item: dict):
        if tenant_id not in self.tenants:
            self.register_tenant(tenant_id, weight=1.0)
        await self.tenants[tenant_id].queue.put(request_item)

    async def schedule_next_job(self) -> dict:
        while True:
            for t_id, t_queue in self.tenants.items():
                if not t_queue.queue.empty():
                    t_queue.deficit += t_queue.quantum
                    peek_item = t_queue.queue._queue[0]
                    cost = peek_item.get("estimated_tokens", 500)
                    
                    if t_queue.deficit >= cost:
                        t_queue.deficit -= cost
                        return await t_queue.queue.get()
            await asyncio.sleep(0.01)
