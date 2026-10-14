import uuid
from datetime import datetime
from decimal import Decimal
from typing import Protocol

from src.payments.domain.entities.currency import Currency
from src.payments.domain.entities.payment_status import PaymentStatus


class PaymentGatewayProtocol(Protocol):
    async def process(
        self,
        payment_id: uuid.UUID,
        idempotency_key: str,
    ) -> PaymentStatus: ...


class NotificationClientProtocol(Protocol):
    async def notify_webhook(
        self,
        webhook_url: str,
        payment_id: uuid.UUID,
        status: PaymentStatus,
        amount: Decimal,
        currency: Currency,
        processed_at: datetime | None,
    ) -> None: ...
