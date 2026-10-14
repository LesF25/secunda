from unittest.mock import AsyncMock, MagicMock, Mock

import pytest

from src.outbox.domain.entities.outbox_message import OutboxMessageEntity
from src.outbox.domain.repositories.outbox import OutboxRepositoryProtocol
from src.payments.application.dto import CreatePaymentDTO
from src.payments.application.queues import PaymentQueue
from src.payments.application.use_cases.create_payment import (
    CreatePaymentUseCase,
)
from src.payments.domain.entities.payment import PaymentEntity
from src.payments.domain.entities.payment_status import PaymentStatus


@pytest.fixture
def m_outbox_repository() -> Mock:
    repository = Mock(spec=OutboxRepositoryProtocol)
    repository.create = AsyncMock()
    return repository


@pytest.fixture
def f_create_use_case(
    m_session_manager: MagicMock,
    m_payment_repository: Mock,
    m_outbox_repository: Mock,
) -> CreatePaymentUseCase:
    return CreatePaymentUseCase(
        session_manager=m_session_manager,
        payment_repository=m_payment_repository,
        outbox_repository=m_outbox_repository,
    )


@pytest.mark.unit
@pytest.mark.asyncio(loop_scope="function")
async def test_new_payment_creates_event(
    f_create_use_case: CreatePaymentUseCase,
    f_create_payment_dto: CreatePaymentDTO,
    f_payment: PaymentEntity,
    m_payment_repository: Mock,
    m_outbox_repository: Mock,
) -> None:
    m_payment_repository.create_or_get.return_value = (f_payment, True)

    result = await f_create_use_case.execute(f_create_payment_dto)

    candidate = m_payment_repository.create_or_get.await_args.args[0]
    assert result is f_payment
    assert candidate.props.idempotency_key == f_create_payment_dto.idempotency_key
    assert candidate.props.status is PaymentStatus.PENDING

    event = m_outbox_repository.create.await_args.args[0]
    assert isinstance(event, OutboxMessageEntity)
    assert event.props.queue_name == PaymentQueue.NEW.value
    assert event.props.payload == {"payment_id": str(f_payment.pk)}


@pytest.mark.unit
@pytest.mark.asyncio(loop_scope="function")
async def test_duplicate_payment_skips_event(
    f_create_use_case: CreatePaymentUseCase,
    f_create_payment_dto: CreatePaymentDTO,
    f_payment: PaymentEntity,
    m_payment_repository: Mock,
    m_outbox_repository: Mock,
) -> None:
    m_payment_repository.create_or_get.return_value = (f_payment, False)

    result = await f_create_use_case.execute(f_create_payment_dto)

    assert result is f_payment
    m_outbox_repository.create.assert_not_awaited()
