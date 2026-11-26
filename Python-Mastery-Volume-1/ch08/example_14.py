"""
Recipe 08.1: Distributed Two-Phase Transaction Rollback Engine
Requires: Python 3.11+
Architecture: Dynamic Multi-Resource Acquisition with Strict LIFO Rollback Guarantees.
"""

from __future__ import annotations
import asyncio
import logging
import uuid
from contextlib import AsyncExitStack
from dataclasses import dataclass
from typing import Protocol

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("transaction.engine")

class DistributedParticipant(Protocol):
    async def prepare(self, tx_id: uuid.UUID) -> bool: ...
    async def commit(self, tx_id: uuid.UUID) -> None: ...
    async def rollback(self, tx_id: uuid.UUID) -> None: ...

@dataclass
class MockSQLParticipant:
    name: str

    async def prepare(self, tx_id: uuid.UUID) -> bool:
        logger.info(f"[{self.name}] PREPARE lock acquired for tx {tx_id}")
        return True

    async def commit(self, tx_id: uuid.UUID) -> None:
        logger.info(f"[{self.name}] COMMIT finalized successfully for tx {tx_id}")

    async def rollback(self, tx_id: uuid.UUID) -> None:
        logger.warning(f"[{self.name}] ROLLBACK executed for tx {tx_id}")

@dataclass
class MockFlakyServiceParticipant:
    name: str
    should_fail: bool = False

    async def prepare(self, tx_id: uuid.UUID) -> bool:
        if self.should_fail:
            logger.error(f"[{self.name}] PREPARE failed: Remote node timed out!")
            raise ConnectionResetError(f"Connection dropped on participant {self.name}")
        logger.info(f"[{self.name}] PREPARE lock acquired for tx {tx_id}")
        return True

    async def commit(self, tx_id: uuid.UUID) -> None:
        logger.info(f"[{self.name}] COMMIT finalized for tx {tx_id}")

    async def rollback(self, tx_id: uuid.UUID) -> None:
        logger.warning(f"[{self.name}] ROLLBACK executed for tx {tx_id}")

class DistributedTransactionCoordinator:
    def __init__(self, participants: list[DistributedParticipant]) -> None:
        self.participants = participants

    async def execute_atomic_transaction(self) -> uuid.UUID:
        tx_id = uuid.uuid4()
        logger.info(f"Starting atomic two-phase commit across {len(self.participants)} nodes. TxID: {tx_id}")

        async with AsyncExitStack() as rollback_stack:
            prepared_nodes: list[DistributedParticipant] = []

            for participant in self.participants:
                # Execute prepare phase
                await participant.prepare(tx_id)
                prepared_nodes.append(participant)

                # Register LIFO rollback hook dynamically in the stack
                # If subsequent participants fail, stack unwinds in reverse order!
                rollback_stack.push_async_callback(participant.rollback, tx_id)

            # All participants prepared cleanly! Now execute COMMIT phase
            logger.info("All participants successfully PREPARED. Proceeding to COMMIT phase.")
            for node in prepared_nodes:
                await node.commit(tx_id)

            # Success! Pop all rollback hooks so they do NOT execute on exit
            rollback_stack.pop_all()
            logger.info(f"Transaction {tx_id} committed atomically across all nodes.")
            return tx_id

# Verification harness
async def main_recipe_08_1() -> None:
    # Scenario A: Clean success
    db1 = MockSQLParticipant("Cluster-Postgres-01")
    db2 = MockSQLParticipant("Cluster-Postgres-02")
    coordinator_ok = DistributedTransactionCoordinator([db1, db2])
    await coordinator_ok.execute_atomic_transaction()

    # Scenario B: Flaky node fails midway through prepare
    print("\n--- Simulating Mid-Transaction Distributed Failure ---")
    bad_node = MockFlakyServiceParticipant("External-Billing-Gateway", should_fail=True)
    coordinator_fail = DistributedTransactionCoordinator([db1, bad_node, db2])
    try:
        await coordinator_fail.execute_atomic_transaction()
    except ConnectionResetError as exc:
        logger.error(f"Coordinator caught anticipated abort: {exc}")
        logger.info("Verifying state: Notice Cluster-Postgres-01 was rolled back automatically!")

if __name__ == "__main__":
    asyncio.run(main_recipe_08_1())
