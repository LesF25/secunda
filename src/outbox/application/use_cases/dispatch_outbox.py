import asyncio
import uuid

import structlog

from src.core.application.transactions import SessionManagerProtocol
from src.outbox.application.interfaces import OutboxPublisherProtocol
from src.outbox.domain.entities.outbox_message import OutboxMessageEntity
from src.outbox.domain.repositories.outbox import (
    OutboxDispatchRepositoryProtocol,
)

logger = structlog.get_logger(__name__)


class OutboxDispatcher:
    MAX_CONCURRENCY = 10
    BATCH_SIZE = 50

    def __init__(
        self,
        repository: OutboxDispatchRepositoryProtocol,
        session_manager: SessionManagerProtocol,
        publisher: OutboxPublisherProtocol,
    ) -> None:
        self._repository = repository
        self._session_manager = session_manager
        self._publisher = publisher
        self._publish_semaphore = asyncio.Semaphore(self.MAX_CONCURRENCY)

    async def dispatch_once(self) -> None:
        lock_token = uuid.uuid4()
        async with self._session_manager:
            messages = await self._repository.lock_batch(
                self.BATCH_SIZE,
                lock_token,
            )

        if not messages:
            return

        logger.info('outbox.fetched', count=len(messages))
        results = await asyncio.gather(
            *(self._publish(message) for message in messages),
            return_exceptions=True,
        )

        published_ids: list[uuid.UUID] = []
        for message, result in zip(messages, results, strict=True):
            if isinstance(result, asyncio.CancelledError):
                raise result

            if isinstance(result, BaseException):
                logger.warning(
                    'outbox.publish_failed',
                    message_id=str(message.pk),
                    queue_name=message.props.queue_name,
                    error=str(result),
                )
                continue

            published_ids.append(message.pk)

        async with self._session_manager:
            await self._repository.delete_published(
                lock_token,
                tuple(published_ids),
            )

    async def _publish(self, message: OutboxMessageEntity) -> None:
        async with self._publish_semaphore:
            await self._publisher.publish(
                queue_name=message.props.queue_name,
                payload=message.props.payload,
                message_id=message.pk,
            )
