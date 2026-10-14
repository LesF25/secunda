import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import delete, or_, select, update

from src.core.infrastructure.repository import SQLAlchemyRepository
from src.outbox.domain.entities.outbox_message import (
    OutboxMessageEntity,
    OutboxMessageProperties,
)
from src.outbox.infrastructure.models import OutboxMessage


class OutboxDispatchRepository(SQLAlchemyRepository):
    LOCK_TTL = timedelta(minutes=1)

    async def lock_batch(
        self,
        batch_size: int,
        lock_token: uuid.UUID,
    ) -> list[OutboxMessageEntity]:
        now = datetime.now(UTC)
        batch_cte = (
            select(OutboxMessage.id)
            .where(
                or_(
                    OutboxMessage.lock_expires_at.is_(None),
                    OutboxMessage.lock_expires_at <= now,
                ),
            )
            .order_by(OutboxMessage.id)
            .with_for_update(skip_locked=True)
            .limit(batch_size)
            .cte('outbox_batch_lock')
        )

        result = await self._session.execute(
            update(OutboxMessage)
            .where(OutboxMessage.id == batch_cte.c.id)
            .values(
                lock_token=lock_token,
                lock_expires_at=now + self.LOCK_TTL,
            )
            .returning(
                OutboxMessage.id,
                OutboxMessage.queue_name,
                OutboxMessage.payload,
            )
        )

        return [
            OutboxMessageEntity(
                pk=row.id,
                props=OutboxMessageProperties(
                    queue_name=row.queue_name,
                    payload=row.payload,
                ),
            )
            for row in result.all()
        ]

    async def delete_published(
        self,
        lock_token: uuid.UUID,
        published_ids: tuple[uuid.UUID, ...],
    ) -> None:
        if not published_ids:
            return

        await self._session.execute(
            delete(OutboxMessage).where(
                OutboxMessage.id.in_(published_ids),
                OutboxMessage.lock_token == lock_token,
            )
        )
