import uuid
from typing import Protocol

from src.outbox.domain.entities.outbox_message import OutboxMessageEntity


class OutboxRepositoryProtocol(Protocol):
    async def create(
        self,
        entity: OutboxMessageEntity,
    ) -> OutboxMessageEntity: ...


class OutboxDispatchRepositoryProtocol(Protocol):
    async def lock_batch(
        self,
        batch_size: int,
        lock_token: uuid.UUID,
    ) -> list[OutboxMessageEntity]: ...

    async def delete_published(
        self,
        lock_token: uuid.UUID,
        published_ids: tuple[uuid.UUID, ...],
    ) -> None: ...
