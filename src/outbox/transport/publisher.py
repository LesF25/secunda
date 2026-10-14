import uuid
from typing import Any

from faststream.rabbit import RabbitBroker


class OutboxPublisher:
    def __init__(
        self,
        broker: RabbitBroker,
        publish_timeout: float = 5.0,
    ) -> None:
        self._broker = broker
        self._publish_timeout = publish_timeout

    async def publish(
        self,
        queue_name: str,
        payload: dict[str, Any],
        message_id: uuid.UUID,
    ) -> None:
        await self._broker.publish(
            payload,
            queue=queue_name,
            message_id=str(message_id),
            persist=True,
            mandatory=True,
            timeout=self._publish_timeout,
        )
