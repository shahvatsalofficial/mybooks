# consumers/dlq_router.py
"""Resilient message retry and Dead-Letter Queue routing engine."""

from __future__ import annotations
import json
import logging
import time
import traceback
from typing import Any

from aiokafka import AIOKafkaProducer

logger = logging.getLogger("dlq_router")


class DeadLetterQueueRouter:
    """Manages retry progression and dead-letter queue routing for poison messages."""

    def __init__(
        self,
        producer: AIOKafkaProducer,
        base_topic: str,
        max_retries: int = 3,
        base_backoff_ms: int = 1000,
    ) -> None:
        self.producer = producer
        self.base_topic = base_topic
        self.max_retries = max_retries
        self.base_backoff_ms = base_backoff_ms
        self.dlq_topic = f"{base_topic}.dlq"

    async def handle_failure(
        self,
        raw_key: bytes | None,
        raw_payload: bytes,
        headers: list[tuple[str, bytes]],
        exception: BaseException,
    ) -> None:
        """Calculates backoff tier and routes message to appropriate retry or DLQ topic."""
        header_dict = {k: v.decode("utf-8") for k, v in headers}
        current_retries = int(header_dict.get("x-retry-count", "0"))

        if current_retries < self.max_retries:
            # Calculate exponential backoff duration: base * 2^retries
            next_retry_count = current_retries + 1
            backoff_delay_ms = self.base_backoff_ms * (2 ** current_retries)
            scheduled_epoch_ms = int(time.time() * 1000) + backoff_delay_ms

            retry_topic = f"{self.base_topic}.retry-{next_retry_count}"
            updated_headers = [
                ("x-retry-count", str(next_retry_count).encode("utf-8")),
                ("x-scheduled-time-ms", str(scheduled_epoch_ms).encode("utf-8")),
                ("x-last-error", str(exception).encode("utf-8")),
            ]

            logger.warning(
                "Routing message key=%s to RETRY topic '%s' (Attempt %d/%d). Delay: %dms",
                raw_key,
                retry_topic,
                next_retry_count,
                self.max_retries,
                backoff_delay_ms,
            )

            await self.producer.send_and_wait(
                topic=retry_topic,
                key=raw_key,
                value=raw_payload,
                headers=updated_headers,
            )

        else:
            # Poison pill threshold exceeded: route permanently to DLQ
            dlq_headers = [
                ("x-retry-count", str(current_retries).encode("utf-8")),
                ("x-dead-letter-timestamp", str(int(time.time())).encode("utf-8")),
                ("x-exception-class", exception.__class__.__name__.encode("utf-8")),
                ("x-exception-message", str(exception).encode("utf-8")),
                ("x-traceback", traceback.format_exc().encode("utf-8")),
            ]

            logger.critical(
                "Message key=%s EXCEEDED max retries (%d). Routing permanently to DEAD-LETTER QUEUE: '%s'",
                raw_key,
                self.max_retries,
                self.dlq_topic,
            )

            await self.producer.send_and_wait(
                topic=self.dlq_topic,
                key=raw_key,
                value=raw_payload,
                headers=dlq_headers,
            )
