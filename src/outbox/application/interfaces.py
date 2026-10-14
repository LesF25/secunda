import uuid
from typing import Any, Protocol


class OutboxPublisherProtocol(Protocol):
    async def publish(
        self,
        queue_name: str,
        payload: dict[str, Any],
        message_id: uuid.UUID,
    ) -> None: ...
