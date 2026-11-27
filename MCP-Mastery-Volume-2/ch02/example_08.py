"""
Multi-Tenant Concurrency & Chaos Verification Test Suite
Author: Vatsal Shah | Vatsal Shah
Simulates 100 concurrent tenant coroutines with random interleaving.
"""

import asyncio
import random
import pytest
from contextvars import ContextVar

TEST_TENANT_CTX: ContextVar[str] = ContextVar("TEST_TENANT_CTX", default="unassigned")

class MockTenantDatabase:
    """Simulates stateful tenant databases with strict isolation tracking."""
    def __init__(self):
        self.tenant_records = {
            f"tenant_{i}": {f"secret_data_for_tenant_{i}"} for i in range(100)
        }
        self.leak_detected = False

    async def query_tenant_data(self, requested_id: str) -> str:
        active_tenant = TEST_TENANT_CTX.get()
        
        # Simulate realistic database I/O latency with random jitter
        await asyncio.sleep(random.uniform(0.010, 0.050))
        
        # Verify active context matches data requested
        if active_tenant != requested_id:
            self.leak_detected = True
            raise ValueError(f"CRITICAL LEAK: Context {active_tenant} accessed data for {requested_id}")
            
        # Check if requested tenant exists
        data = self.tenant_records.get(active_tenant)
        if not data:
            raise KeyError(f"Unknown tenant: {active_tenant}")
            
        return list(data)[0]


async def simulate_agent_worker(db: MockTenantDatabase, tenant_id: str, iterations: int = 10):
    """Simulates an autonomous agent making repeated tool calls."""
    token = TEST_TENANT_CTX.set(tenant_id)
    try:
        for _ in range(iterations):
            # Perform tool call
            result = await db.query_tenant_data(tenant_id)
            assert tenant_id in result, f"Data integrity failure: {result}"
            # Simulate thinking time between tool calls
            await asyncio.sleep(random.uniform(0.005, 0.020))
    finally:
        TEST_TENANT_CTX.reset(token)


@pytest.mark.asyncio
async def test_high_concurrency_tenant_isolation():
    """Execute 100 concurrent tenant agents performing 1,000 total tool queries."""
    db = MockTenantDatabase()
    tasks = [
        asyncio.create_task(simulate_agent_worker(db, f"tenant_{i}", iterations=10))
        for i in range(100)
    ]
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Check for any exceptions or context leaks
    for idx, r in enumerate(results):
        if isinstance(r, Exception):
            pytest.fail(f"Tenant worker {idx} failed with error: {r}")
            
    assert not db.leak_detected, "Concurrency test detected cross-tenant context bleed!"
    print("\n✅ Concurrency Chaos Test Passed: 1,000 queries with 0 context leaks.")
