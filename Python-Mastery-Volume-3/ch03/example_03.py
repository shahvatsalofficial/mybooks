# consumers/kafka_consumer.py
"""Production-grade asynchronous Kafka consumer with cooperative rebalancing."""

from __future__ import annotations
import asyncio
from collections.abc import AsyncIterator
import logging
import signal
import sys
from typing import Any

from aiokafka import AIOKafkaConsumer, ConsumerRecord, TopicPartition
from aiokafka.errors import KafkaError

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("kafka_consumer")


class RebalanceListener:
    """Monitors partition assignments and revocations during consumer group rebalances."""

    def on_partitions_revoked(self, revoked: set[TopicPartition]) -> None:
        revoked_str = ", ".join(f"{tp.topic}:{tp.partition}" for tp in revoked)
        logger.warning("Consumer partitions REVOKED during rebalance: [%s]", revoked_str)

    def on_partitions_assigned(self, assigned: set[TopicPartition]) -> None:
        assigned_str = ", ".join(f"{tp.topic}:{tp.partition}" for tp in assigned)
        logger.info("Consumer partitions ASSIGNED: [%s]", assigned_str)


class ResilientEventConsumer:
    """Manages asynchronous Kafka consumption lifecycle with manual commit boundaries."""

    def __init__(
        self,
        bootstrap_servers: str,
        topic: str,
        group_id: str,
    ) -> None:
        self.bootstrap_servers = bootstrap_servers
        self.topic = topic
        self.group_id = group_id
        self._running = False
        self._consumer: AIOKafkaConsumer | None = None

    async def start(self) -> None:
        """Initializes socket connections and joins the distributed consumer group."""
        listener = RebalanceListener()
        self._consumer = AIOKafkaConsumer(
            self.topic,
            bootstrap_servers=self.bootstrap_servers,
            group_id=self.group_id,
            enable_auto_commit=False,  # CRITICAL: Strict manual offset commitment
            auto_offset_reset="earliest",
            max_poll_interval_ms=300000,  # 5 minutes maximum processing duration
            max_poll_records=100,         # Tuned batch ceiling
            partition_assignment_strategy=["cooperative-sticky"],
        )
        await self._consumer.start()
        self._running = True
        logger.info("AIOKafka consumer successfully joined group '%s' for topic '%s'", self.group_id, self.topic)

    async def stop(self) -> None:
        """Gracefully drains active processing and releases consumer group partitions."""
        logger.info("Commencing graceful consumer shutdown...")
        self._running = False
        if self._consumer:
            await self._consumer.stop()
            logger.info("Consumer stopped safely. Partitions released.")

    async def consume_loop(self) -> None:
        """Main event consumption loop processing records with manual offset commits."""
        assert self._consumer is not None, "Consumer must be started before consuming."

        while self._running:
            try:
                # Fetch a batch of records cooperatively without blocking the event loop
                batch_data = await self._consumer.getmany(timeout_ms=1000, max_records=100)
                if not batch_data:
                    continue

                for tp, records in batch_data.items():
                    logger.info("Processing batch of %d records from %s:%d", len(records), tp.topic, tp.partition)
                    
                    for record in records:
                        await self._process_single_record(record)

                    # Atomically commit the highest processed offset for this partition
                    highest_offset = records[-1].offset + 1
                    await self._consumer.commit({tp: highest_offset})
                    logger.debug("Committed offset %d on partition %s:%d", highest_offset, tp.topic, tp.partition)

            except KafkaError as err:
                logger.error("Transient Kafka communication error encountered: %s", err, exc_info=True)
                await asyncio.sleep(2.0)
            except Exception as exc:
                logger.critical("Fatal unhandled exception in consumer loop: %s", exc, exc_info=True)
                await asyncio.sleep(5.0)

    async def _process_single_record(self, record: ConsumerRecord) -> None:
        """Executes transactional business logic for an individual event record."""
        # Deserialize payload and enforce domain invariants
        key = record.key.decode("utf-8") if record.key else "UNKNOWN_KEY"
        logger.debug("Executing domain business rules for record key=%s offset=%d", key, record.offset)
        # Simulate business computation
        await asyncio.sleep(0.01)
