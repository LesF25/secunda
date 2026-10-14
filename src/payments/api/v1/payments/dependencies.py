from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.infrastructure.connection import get_session
from src.core.infrastructure.session_managers import TransactionSessionManager
from src.outbox.infrastructure.repositories.outbox_message_repository import (
    OutboxRepository,
)
from src.payments.application.use_cases.create_payment import (
    CreatePaymentUseCase,
)
from src.payments.application.use_cases.retrieve_payment import (
    RetrievePaymentUseCase,
)
from src.payments.infrastructure.repositories.payment_repository import (
    PaymentRepository,
)


def get_create_payment_use_case(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> CreatePaymentUseCase:
    return CreatePaymentUseCase(
        session_manager=TransactionSessionManager(session),
        payment_repository=PaymentRepository(session),
        outbox_repository=OutboxRepository(session),
    )


def get_retrieve_payment_use_case(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> RetrievePaymentUseCase:
    return RetrievePaymentUseCase(
        payment_repository=PaymentRepository(session),
    )
