import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import DateTime, Numeric, String, Uuid, func, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from src.core.infrastructure.models import Base
from src.payments.domain.entities.currency import Currency
from src.payments.domain.entities.payment_status import PaymentStatus


class Payment(Base):
    __tablename__ = 'payments'

    idempotency_key: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        unique=True,
        nullable=False,
    )
    amount: Mapped[Decimal] = mapped_column(
        Numeric(precision=10, scale=2),
        nullable=False
    )
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    webhook_url: Mapped[str] = mapped_column(String(2048), nullable=False)
    currency: Mapped[Currency] = mapped_column(String(3), nullable=False)
    status: Mapped[PaymentStatus] = mapped_column(
        String(20),
        nullable=False,
        server_default=text("'pending'"),
    )
    meta_data: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default=text("'{}'::jsonb"),
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.clock_timestamp(),
    )
    processed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
