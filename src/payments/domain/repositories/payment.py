import uuid
from datetime import datetime
from typing import Protocol

from src.payments.domain.entities.payment import PaymentEntity
from src.payments.domain.entities.payment_status import PaymentStatus


class PaymentRepositoryProtocol(Protocol):
    async def create_or_get(
        self,
        entity: PaymentEntity,
    ) -> tuple[PaymentEntity, bool]: ...

    async def get_by_id(
        self,
        payment_id: uuid.UUID,
    ) -> PaymentEntity | None: ...

    async def set_result_or_get(
        self,
        payment_id: uuid.UUID,
        status: PaymentStatus,
        processed_at: datetime,
    ) -> PaymentEntity | None: ...
