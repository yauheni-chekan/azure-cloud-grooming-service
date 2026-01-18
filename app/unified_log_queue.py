"""Unified logging via Azure Storage Queue.

This module provides a best-effort "unified log" sender. Failures to emit logs
must never break API requests.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from functools import lru_cache
from typing import Any

import anyio
from azure.core.exceptions import ResourceExistsError
from azure.storage.queue import QueueClient

from app.config import settings

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class UnifiedLogEvent:
    """A minimal, JSON-serializable unified log event."""

    level: str
    event: str
    message: str
    timestamp: str
    service: str
    version: str
    context: dict[str, Any]


class UnifiedLogQueueSender:
    """Best-effort sender for unified log events to an Azure Storage Queue."""

    def __init__(self, connection_string: str, queue_name: str) -> None:
        self._connection_string = connection_string
        self._queue_name = queue_name

    def _client(self) -> QueueClient:
        return QueueClient.from_connection_string(
            conn_str=self._connection_string,
            queue_name=self._queue_name,
        )

    def _ensure_queue(self, client: QueueClient) -> None:
        try:
            client.create_queue()
        except ResourceExistsError:
            return
        except Exception:
            # If we can't create it (permissions/policy), try sending anyway.
            logger.debug("Could not create unified logs queue %s", self._queue_name, exc_info=True)

    async def send(self, *, level: str, event: str, message: str, **context: Any) -> None:
        """Send a unified log event. Never raises."""
        if not self._connection_string:
            return

        payload = UnifiedLogEvent(
            level=level,
            event=event,
            message=message,
            timestamp=datetime.now(UTC).isoformat(),
            service=settings.app_name,
            version=settings.app_version,
            context=context,
        )

        body = json.dumps(payload.__dict__, ensure_ascii=False, separators=(",", ":"))

        try:
            client = self._client()
            self._ensure_queue(client)
            await anyio.to_thread.run_sync(client.send_message, body)
        except Exception:
            logger.debug("Failed to send unified log event", exc_info=True)


@lru_cache(maxsize=1)
def get_unified_log_sender() -> UnifiedLogQueueSender | None:
    """Return a singleton unified log sender, if configured."""
    if not settings.unified_logs_storage_connection_string:
        return None
    return UnifiedLogQueueSender(
        connection_string=settings.unified_logs_storage_connection_string,
        queue_name=settings.unified_logs_storage_queue_name,
    )


log_sender = get_unified_log_sender()
