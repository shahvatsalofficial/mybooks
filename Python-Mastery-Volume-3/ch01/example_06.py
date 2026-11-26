# infrastructure/event_bus.py
"""Asynchronous in-process domain event dispatcher and subscription router."""

from __future__ import annotations
import asyncio
from collections import defaultdict
from collections.abc import Callable, Coroutine
import logging
from typing import Any, TypeVar

from domain.model import DomainEvent

logger = logging.getLogger(__name__)

E = TypeVar("E", bound=DomainEvent)
EventHandler = Callable[[E], Coroutine[Any, Any, None]]


class AsyncEventDispatcher:
    """Central asynchronous message bus registering and dispatching domain events."""

    def __init__(self) -> None:
        self._handlers: dict[type[DomainEvent], list[EventHandler[Any]]] = defaultdict(list)

    def subscribe(self, event_type: type[E], handler: EventHandler[E]) -> None:
        """Register an asynchronous subscriber callback for a specific event type."""
        self._handlers[event_type].append(handler)
        logger.info(
            "Registered handler '%s' for event type '%s'",
            handler.__name__,
            event_type.__name__,
        )

    async def dispatch(self, events: list[DomainEvent]) -> None:
        """Execute all registered subscribers concurrently across independent error boundaries."""
        for event in events:
            handlers = self._handlers.get(type(event), [])
            if not handlers:
                logger.debug("Zero subscribers found for event '%s'", type(event).__name__)
                continue

            # Execute all subscriber tasks concurrently using asyncio.gather
            tasks = [self._execute_safe(handler, event) for handler in handlers]
            await asyncio.gather(*tasks)

    async def _execute_safe(self, handler: EventHandler[Any], event: DomainEvent) -> None:
        """Isolate handler exceptions to prevent cascading failures."""
        try:
            await handler(event)
            logger.debug(
                "Successfully executed handler '%s' for event '%s'",
                handler.__name__,
                type(event).__name__,
            )
        except Exception:
            logger.exception(
                "Unhandled exception in subscriber '%s' processing event '%s'",
                handler.__name__,
                type(event).__name__,
            )
