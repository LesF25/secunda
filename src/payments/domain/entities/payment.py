import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from src.core.domain.entities.entity import AggregateRoot
from src.payments.domain.entities.currency import Currency
from src.payments.domain.entities.payment_status import PaymentStatus


@dataclass(frozen=True)
class PaymentProperties:
    amount: Decimal
    description: str
    meta_data: dict[str, Any]
    currency: Currency
    status: PaymentStatus
    idempotency_key: uuid.UUID
    webhook_url: str
    created_at: datetime = field(
        default_factory=(
            lambda: datetime.now(timezone.utc).replace(microsecond=0)
        )
    )
    processed_at: datetime | None = None


class PaymentEntity(
    AggregateRoot[uuid.UUID, PaymentProperties]
):
    @classmethod
    def create(
        cls,
        amount: Decimal,
        description: str,
        meta_data: dict[str, Any],
        currency: Currency,
        status: PaymentStatus,
        idempotency_key: uuid.UUID,
        webhook_url: str,
    ) -> 'PaymentEntity':
        return cls(
            pk=cls._get_entity_id(),
            props=PaymentProperties(
                amount=amount,
                description=description,
                meta_data=meta_data,
                currency=currency,
                status=status,
                idempotency_key=idempotency_key,
                webhook_url=webhook_url,
            )
        )
