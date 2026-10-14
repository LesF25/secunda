from collections.abc import Sequence
from typing import Any

import structlog
from faststream.rabbit import RabbitBroker, RabbitMessage, RabbitQueue

logger = structlog.get_logger(__name__)


class PaymentPublisher:
    def __init__(self, broker: RabbitBroker):
        self._broker = broker

    async def publish_event(
        self,
        queue_name: str,
        payload: Any,
        message_id: str,
        headers: dict,
    ) -> None:
        await self._broker.publish(
            payload,
            queue=queue_name,
            message_id=message_id,
            headers=headers,
            persist=True,
            mandatory=True,
            timeout=5.0,
        )


class PaymentRetryPublisher:
    RETRY_ATTEMPT_HEADER = 'x-retry-attempt'
    MAX_ATTEMPTS = 3

    def __init__(
        self,
        publisher: PaymentPublisher,
        retry_queues: Sequence[RabbitQueue],
    ) -> None:
        self._publisher = publisher
        self._retry_queues = retry_queues

    async def publish_with_retry(
        self,
        message: RabbitMessage,
        error: Exception,
    ) -> bool:
        try:
            attempt = max(
                1,
                int(message.headers.get(self.RETRY_ATTEMPT_HEADER, 1)),
            )
        except (TypeError, ValueError):
            attempt = 1

        if attempt >= self.MAX_ATTEMPTS:
            logger.error(
                'payment.processing_exhausted',
                message_id=message.message_id,
                attempt=attempt,
                error=str(error),
            )
            return False

        retry_queue = self._retry_queues[attempt - 1]

        try:
            payload = await message.decode()
            await self._publisher.publish_event(
                queue_name=retry_queue.name,
                payload=payload,
                message_id=message.message_id,
                headers={
                    **message.headers,
                    self.RETRY_ATTEMPT_HEADER: attempt + 1,
                },
            )
        except Exception as publish_error:
            logger.error(
                'payment.retry_publish_failed',
                message_id=message.message_id,
                attempt=attempt,
                retry_queue=retry_queue.name,
                error=str(publish_error),
            )
            raise

        logger.warning(
            'payment.retry_scheduled',
            message_id=message.message_id,
            next_attempt=attempt + 1,
            retry_queue=retry_queue.name,
            error=str(error),
        )
        return True
