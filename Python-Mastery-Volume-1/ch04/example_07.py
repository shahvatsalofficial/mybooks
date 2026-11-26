"""
Recipe 04.1: Resilient Structured Microservice Pipeline
File: recipe_04_1_taskgroup_orchestrator.py
Python Version: 3.12+
"""

from __future__ import annotations
import asyncio
import logging
import random
import time
from typing import NamedTuple, Any

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("MicroserviceOrchestrator")


class ServiceResponse(NamedTuple):
    service_name: str
    data: dict[str, Any]
    latency_ms: float


class UpstreamServiceError(Exception):
    """Raised when an upstream service fails definitively."""
    pass


async def call_upstream_with_retry(
    service_name: str,
    endpoint: str,
    max_retries: int = 3,
    base_backoff_sec: float = 0.2,
    timeout_sec: float = 1.5,
) -> ServiceResponse:
    """Executes an async call with strict timeout governance and jittered backoff."""
    for attempt in range(1, max_retries + 1):
        start_time = time.perf_counter()
        try:
            # Python 3.11+ context-managed deadline timeout
            async with asyncio.timeout(timeout_sec):
                logger.info(f"[{service_name}] Invoking {endpoint} (Attempt {attempt}/{max_retries})...")
                
                # Simulate network latency and intermittent failures
                await asyncio.sleep(random.uniform(0.1, 0.4))
                if service_name == "FraudEngine" and attempt < 2:
                    raise ConnectionResetError("Transient network drop")

                latency = (time.perf_counter() - start_time) * 1000
                return ServiceResponse(service_name, {"status": "SUCCESS", "id": random.randint(1000, 9999)}, latency)

        except TimeoutError:
            logger.warning(f"[{service_name}] Execution exceeded {timeout_sec}s deadline.")
            if attempt == max_retries:
                raise UpstreamServiceError(f"{service_name} timed out after {max_retries} attempts.")
        except ConnectionResetError as e:
            logger.warning(f"[{service_name}] Connection error on attempt {attempt}: {e}")
            if attempt == max_retries:
                raise UpstreamServiceError(f"{service_name} failed: {e}")

        # Full jitter exponential backoff formula: sleep = rand(0, base * 2^attempt)
        backoff = random.uniform(0, base_backoff_sec * (2 ** attempt))
        logger.info(f"[{service_name}] Sleeping for {backoff:.3f}s before retry...")
        await asyncio.sleep(backoff)

    raise UpstreamServiceError(f"{service_name} exhausted all retries.")


async def execute_order_checkout(order_id: str) -> dict[str, Any]:
    """Coordinates parallel child tasks inside a structured TaskGroup boundary."""
    results: list[ServiceResponse] = []
    
    logger.info(f"Starting structured order checkout: {order_id}")
    
    try:
        async with asyncio.TaskGroup() as tg:
            # Spawn parallel child tasks
            t_user = tg.create_task(call_upstream_with_retry("UserAuth", "/v1/auth"))
            t_inv = tg.create_task(call_upstream_with_retry("Inventory", "/v2/reserve"))
            t_fraud = tg.create_task(call_upstream_with_retry("FraudEngine", "/v1/verify"))

        # Execution ONLY reaches here if ALL tasks succeed
        results = [t_user.result(), t_inv.result(), t_fraud.result()]
        logger.info("All microservice dependencies completed successfully.")
        return {
            "order_id": order_id,
            "status": "APPROVED",
            "services": {r.service_name: r.data for r in results},
        }

    except* UpstreamServiceError as eg:
        # PEP 654 exception* catches specific failures from TaskGroup
        logger.error(f"Checkout aborted due to upstream failures: {eg.exceptions}")
        raise
    except* asyncio.CancelledError:
        logger.warning("Checkout pipeline received cancellation signal; tearing down cleanly.")
        raise


if __name__ == "__main__":
    try:
        outcome = asyncio.run(execute_order_checkout("ORD-89412"))
        print("\nCheckout Outcome:", outcome)
    except Exception as exc:
        print("\nCheckout Failed Catastrophically:", exc)
