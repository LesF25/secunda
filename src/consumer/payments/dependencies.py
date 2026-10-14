from typing import Annotated

import aiohttp
from faststream import Context, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.infrastructure.connection import get_session
from src.core.infrastructure.session_managers import TransactionSessionManager
from src.payments.application.use_cases.process_payment import (
    ProcessPaymentUseCase,
)
from src.payments.infrastructure.clients.webhook import WebhookNotificationClient
from src.payments.infrastructure.gateways.simulated import SimulatedPaymentGateway
from src.payments.infrastructure.repositories.payment_repository import (
    PaymentRepository,
)

payment_gateway = SimulatedPaymentGateway()


async def get_process_payment_use_case(
    session: Annotated[AsyncSession, Depends(get_session)],
    http_session: aiohttp.ClientSession = Context('http_session'),
) -> ProcessPaymentUseCase:
    return ProcessPaymentUseCase(
        payment_repository=PaymentRepository(session),
        session_manager=TransactionSessionManager(session),
        payment_gateway=payment_gateway,
        notification_client=WebhookNotificationClient(http_session),
    )
