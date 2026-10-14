import uuid
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from src.payments.domain.entities.currency import Currency


@dataclass(frozen=True, slots=True)
class CreatePaymentDTO:
    idempotency_key: uuid.UUID
    amount: Decimal
    currency: Currency
    description: str
    webhook_url: str
    meta_data: dict[str, Any]


@dataclass(frozen=True, slots=True)
class RetrievePaymentDTO:
    payment_id: uuid.UUID
