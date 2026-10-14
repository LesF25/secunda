from typing import Any, cast

from faststream import BaseMiddleware, StreamMessage
from faststream.rabbit import RabbitBroker, RabbitMessage
from faststream.types import AsyncFuncAny

from src.consumer.payments.declarations import payments_retry_queues
from src.consumer.payments.publisher import (
    PaymentPublisher,
    PaymentRetryPublisher,
)


class RetryMiddleware(BaseMiddleware):
    async def consume_scope(
        self,
        call_next: AsyncFuncAny,
        msg: StreamMessage,
    ) -> Any:
        try:
            result = await call_next(msg)
        except Exception as exc:
            msg = cast(RabbitMessage, msg)
            await self._handle_exception(msg, exc)
            return None

        await cast(RabbitMessage, msg).ack()
        return result

    async def _handle_exception(
        self,
        message: RabbitMessage,
        exc: Exception,
    ) -> None:
        retry_publisher = self._retry_publisher

        try:
            is_scheduled = await retry_publisher.publish_with_retry(message, exc)
        except Exception:
            await message.nack(requeue=True)
            return

        if not is_scheduled:
            await message.reject(requeue=False)
            return

        await message.ack()

    @property
    def _retry_publisher(self) -> PaymentRetryPublisher:
        broker: RabbitBroker = self.context.get('broker')
        return PaymentRetryPublisher(
            PaymentPublisher(broker),
            payments_retry_queues,
        )
