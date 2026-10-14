import uuid
from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert

from src.core.infrastructure.repository import SQLAlchemyRepository
from src.payments.domain.entities.currency import Currency
from src.payments.domain.entities.payment import PaymentEntity, PaymentProperties
from src.payments.domain.entities.payment_status import PaymentStatus
from src.payments.infrastructure.models import Payment


class PaymentMapper:
    def to_entity(self, orm: Payment) -> PaymentEntity:
        return PaymentEntity(
            orm.id,
            PaymentProperties(
                idempotency_key=orm.idempotency_key,
                amount=orm.amount,
                description=orm.description,
                webhook_url=orm.webhook_url,
                currency=Currency(orm.currency),
                status=PaymentStatus(orm.status),
                meta_data=orm.meta_data,
                created_at=orm.created_at,
                processed_at=orm.processed_at,
            )
        )


class PaymentRepository(SQLAlchemyRepository):
    MAPPER = PaymentMapper()

    async def create_or_get(
        self,
        entity: PaymentEntity,
    ) -> tuple[PaymentEntity, bool]:
        props = entity.props

        result = await self._session.execute(
            insert(Payment)
            .values(
                id=entity.pk,
                idempotency_key=props.idempotency_key,
                amount=props.amount,
                description=props.description,
                webhook_url=props.webhook_url,
                currency=props.currency,
                status=props.status,
                meta_data=props.meta_data,
                created_at=props.created_at,
                processed_at=props.processed_at,
            )
            .on_conflict_do_nothing(
                index_elements=[Payment.idempotency_key],
            )
            .returning(Payment)
        )

        payment = result.scalar_one_or_none()
        if payment is not None:
            return self.MAPPER.to_entity(payment), True

        existing = await self._get_by_idempotency_key(props.idempotency_key)
        return existing, False

    async def get_by_id(
        self,
        payment_id: uuid.UUID,
    ) -> PaymentEntity | None:
        result = await self._session.execute(
            select(Payment)
            .where(Payment.id == payment_id)
        )
        payment = result.scalar_one_or_none()

        if payment is None:
            return None

        return self.MAPPER.to_entity(payment)

    async def set_result_or_get(
        self,
        payment_id: uuid.UUID,
        status: PaymentStatus,
        processed_at: datetime,
    ) -> PaymentEntity | None:
        result = await self._session.execute(
            update(Payment)
            .where(
                Payment.id == payment_id,
                Payment.status == PaymentStatus.PENDING,
            )
            .values(
                status=status,
                processed_at=processed_at,
            )
            .returning(Payment)
        )
        payment = result.scalar_one_or_none()

        if payment is None:
            return await self.get_by_id(payment_id)

        return self.MAPPER.to_entity(payment)


    async def _get_by_idempotency_key(
        self,
        idempotency_key: uuid.UUID,
    ) -> PaymentEntity:
        result = await self._session.execute(
            select(Payment)
            .where(
                Payment.idempotency_key == idempotency_key,
            ),
        )
        payment = result.scalar_one()

        return self.MAPPER.to_entity(payment)
