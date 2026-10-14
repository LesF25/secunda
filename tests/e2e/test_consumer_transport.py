import uuid
from unittest.mock import AsyncMock, Mock

import pytest
from fast_depends import dependency_provider
from faststream.rabbit import TestRabbitBroker

from src.consumer.main import broker
from src.consumer.payments.declarations import payments_queue
from src.consumer.payments.dependencies import get_process_payment_use_case
from src.payments.application.use_cases.process_payment import (
    ProcessPaymentUseCase,
)


@pytest.mark.e2e
@pytest.mark.asyncio(loop_scope="function")
async def test_message_calls_use_case() -> None:
    payment_id = uuid.uuid4()
    m_use_case = Mock(spec=ProcessPaymentUseCase)
    m_use_case.execute = AsyncMock()

    def override_use_case() -> Mock:
        return m_use_case

    with dependency_provider.scope(
        get_process_payment_use_case,
        override_use_case,
    ):
        async with TestRabbitBroker(
            broker,
            connect_only=False,
        ) as test_broker:
            await test_broker.publish(
                {"payment_id": str(payment_id)},
                queue=payments_queue,
            )

    m_use_case.execute.assert_awaited_once_with(payment_id)
