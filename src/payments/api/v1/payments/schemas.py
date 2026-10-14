import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field, HttpUrl

from src.payments.domain.entities.payment import PaymentEntity
from src.payments.domain.entities.currency import Currency
from src.payments.domain.entities.payment_status import PaymentStatus


class PaymentRequest(BaseModel):
    amount: Decimal = Field(gt=0, max_digits=10, decimal_places=2)
    currency: Currency
    description: str = Field(min_length=1, max_length=255)
    meta_data: dict[str, Any] = Field(default_factory=dict)
    webhook_url: HttpUrl


class PaymentResponse(BaseModel):
    payment_id: uuid.UUID
    status: PaymentStatus
    created_at: datetime

    @classmethod
    def from_entity(cls, entity: PaymentEntity) -> 'PaymentResponse':
        return cls(
            payment_id=entity.pk,
            status=entity.props.status,
            created_at=entity.props.created_at,
        )


class PaymentDetailResponse(BaseModel):
    payment_id: uuid.UUID
    idempotency_key: uuid.UUID
    amount: Decimal
    currency: Currency
    description: str
    status: PaymentStatus
    webhook_url: HttpUrl
    meta_data: dict[str, Any]
    created_at: datetime
    processed_at: datetime | None = None

    @classmethod
    def from_entity(cls, entity: PaymentEntity) -> 'PaymentDetailResponse':
        props = entity.props
        return cls(
            payment_id=entity.pk,
            idempotency_key=props.idempotency_key,
            amount=props.amount,
            currency=props.currency,
            description=props.description,
            status=props.status,
            webhook_url=HttpUrl(props.webhook_url),
            meta_data=props.meta_data,
            created_at=props.created_at,
            processed_at=props.processed_at,
        )
