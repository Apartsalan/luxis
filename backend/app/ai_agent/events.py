"""Event bus — async in-process event system for the orchestrator.

Connects classification, payments, pipeline steps, and deadlines
to automated actions without external dependencies (no Redis/Celery).
"""

import logging
from collections import defaultdict
from typing import Any, Callable, Coroutine

logger = logging.getLogger(__name__)

# Event name constants
EMAIL_CLASSIFIED = "email.classified"
PAYMENT_RECEIVED = "payment.received"
STEP_CHANGED = "step.changed"
DEADLINE_REACHED = "deadline.reached"
TASK_COMPLETED = "task.completed"


class EventBus:
    """Simple async event bus. Singleton per application."""

    def __init__(self) -> None:
        self._handlers: dict[str, list[Callable[..., Coroutine[Any, Any, None]]]] = defaultdict(list)

    def on(self, event: str, handler: Callable[..., Coroutine[Any, Any, None]]) -> None:
        """Register a handler for an event."""
        self._handlers[event].append(handler)
        logger.info("EventBus: registered handler %s for %s", handler.__name__, event)

    async def emit(self, event: str, **kwargs: Any) -> None:
        """Fire an event. Handlers run sequentially; failures are logged, never propagated."""
        handlers = self._handlers.get(event, [])
        if not handlers:
            return

        for handler in handlers:
            try:
                await handler(**kwargs)
            except Exception:
                logger.exception(
                    "EventBus: handler %s failed for event %s",
                    handler.__name__,
                    event,
                )

    def clear(self) -> None:
        """Remove all handlers. For testing only."""
        self._handlers.clear()


# Module-level singleton
event_bus = EventBus()
