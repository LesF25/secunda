from sqlalchemy import insert

from src.core.infrastructure.repository import SQLAlchemyRepository
from src.outbox.domain.entities.outbox_message import OutboxMessageProperties
from src.outbox.domain.entities.outbox_message import OutboxMessageEntity
from src.outbox.infrastructure.models import OutboxMessage


class OutboxMapper:
    def to_entity(
        self,
        orm: OutboxMessage,
    ) -> OutboxMessageEntity:
        return OutboxMessageEntity(
            orm.id,
            OutboxMessageProperties(
                queue_name=orm.queue_name,
                payload=orm.payload,
            ),
        )


class OutboxRepository(SQLAlchemyRepository):
    MAPPER = OutboxMapper()

    async def create(
        self,
        entity: OutboxMessageEntity,
    ) -> OutboxMessageEntity:
        props = entity.props
        result = await self._session.execute(
            insert(OutboxMessage)
            .values(
                id=entity.pk,
                queue_name=props.queue_name,
                payload=props.payload,
            )
            .returning(OutboxMessage),
        )
        payment = result.scalar_one()

        return self.MAPPER.to_entity(payment)
