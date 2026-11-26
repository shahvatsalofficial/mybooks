"""
Multi-Region Failover Dispatcher with Circuit Breaking and Spillover
Enterprise-grade Python 3.12 implementation utilizing HTTPX with connection pooling.
"""
import time
import logging
from typing import List, Dict, Any, Optional
import httpx

logger = logging.getLogger("multi_region_router")

class RegionalEndpoint:
    def __init__(self, name: str, base_url: str, api_key: str, priority: int = 1):
        self.name = name
        self.base_url = base_url
        self.api_key = api_key
        self.priority = priority
        self.is_healthy = True
        self.consecutive_failures = 0
        self.rate_limited_until = 0.0

    def mark_success(self):
        self.consecutive_failures = 0
        self.is_healthy = True

    def mark_rate_limited(self, retry_after_seconds: float = 5.0):
        self.rate_limited_until = time.time() + retry_after_seconds
        logger.warning(f"Endpoint {self.name} rate-limited. Backing off for {retry_after_seconds}s")

    def mark_failure(self):
        self.consecutive_failures += 1
        if self.consecutive_failures >= 3:
            self.is_healthy = False
            logger.error(f"CIRCUIT BROKEN: Endpoint {self.name} disabled due to 3 consecutive failures.")

    def is_available(self) -> bool:
        if not self.is_healthy:
            return False
        if time.time() < self.rate_limited_until:
            return False
        return True

class MultiRegionAIRouter:
    def __init__(self, endpoints: List[RegionalEndpoint]):
        self.endpoints = sorted(endpoints, key=lambda e: e.priority)
        self.client = httpx.Client(
            timeout=httpx.Timeout(30.0, connect=5.0),
            limits=httpx.Limits(max_connections=200, max_keepalive_connections=50)
        )

    def dispatch_request(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        last_exception = None
        for endpoint in self.endpoints:
            if not endpoint.is_available():
                continue

            url = f"{endpoint.base_url}/openai/deployments/gpt-4o/chat/completions?api-version=2024-08-01-preview"
            headers = {
                "api-key": endpoint.api_key,
                "Content-Type": "application/json"
            }

            try:
                response = self.client.post(url, headers=headers, json=payload)
                
                if response.status_code == 200:
                    endpoint.mark_success()
                    return response.json()
                    
                elif response.status_code == 429:
                    retry_after = float(response.headers.get("Retry-After", 3.0))
                    endpoint.mark_rate_limited(retry_after)
                    logger.info(f"Failing over to next region due to 429 on {endpoint.name}")
                    continue
                    
                elif response.status_code >= 500:
                    endpoint.mark_failure()
                    logger.warning(f"5xx Server error on {endpoint.name}: Status {response.status_code}")
                    continue
                else:
                    response.raise_for_status()

            except (httpx.ConnectError, httpx.TimeoutException) as exc:
                endpoint.mark_failure()
                last_exception = exc
                logger.error(f"Network transport timeout connecting to {endpoint.name}")
                continue

        raise RuntimeError(f"CRITICAL: All regional AI endpoints exhausted or offline. Last error: {last_exception}")
