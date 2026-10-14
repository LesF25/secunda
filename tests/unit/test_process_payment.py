import uuid
from dataclasses import replace
from datetime import UTC, datetime
from unittest.mock import ANY, AsyncMock, MagicMock, Mock

import pytest

from src.payments.application.interfaces import (
    NotificationClientProtocol,
    PaymentGatewayProtocol,
)
from src.payments.application.use_cases.process_payment import (
    PaymentNotFoundError,
    PaymentProcessingConflictError,
    ProcessPaymentUseCase,
)
from src.payments.domain.entities.payment import PaymentEntity
from src.payments.domain.entities.payment_status import PaymentStatus


@pytest.fixture
def f_processed_payment(f_payment: PaymentEntity) -> PaymentEntity:
    return PaymentEntity(
        pk=f_payment.pk,
        props=replace(
            f_payment.props,
            status=PaymentStatus.SUCCEEDED,
            processed_at=datetime(2026, 10, 13, 8, 31, tzinfo=UTC),
        ),
    )


@pytest.fixture
def m_payment_gateway() -> Mock:
    gateway = Mock(spec=PaymentGatewayProtocol)
    gateway.process = AsyncMock()
    return gateway


@pytest.fixture
def m_notification_client() -> Mock:
    client = Mock(spec=NotificationClientProtocol)
    client.notify_webhook = AsyncMock()
    return client


@pytest.fixture
def f_process_use_case(
    m_payment_repository: Mock,
    m_session_manager: MagicMock,
    m_payment_gateway: Mock,
    m_notification_client: Mock,
) -> ProcessPaymentUseCase:
    return ProcessPaymentUseCase(
        payment_repository=m_payment_repository,
        session_manager=m_session_manager,
        payment_gateway=m_payment_gateway,
        notification_client=m_notification_client,
    )


@pytest.mark.unit
@pytest.mark.asyncio(loop_scope="function")
async def test_pending_payment_notifies_result(
    f_process_use_case: ProcessPaymentUseCase,
    f_payment: PaymentEntity,
    f_processed_payment: PaymentEntity,
    m_payment_repository: Mock,
    m_payment_gateway: Mock,
    m_notification_client: Mock,
) -> None:
    m_payment_repository.get_by_id.return_value = f_payment
    m_payment_gateway.process.return_value = PaymentStatus.SUCCEEDED
    m_payment_repository.set_result_or_get.return_value = f_processed_payment

    await f_process_use_case.execute(f_payment.pk)

    m_payment_gateway.process.assert_awaited_once_with(
        payment_id=f_payment.pk,
        idempotency_key=str(f_payment.pk),
    )
    m_payment_repository.set_result_or_get.assert_awaited_once_with(
        f_payment.pk,
        PaymentStatus.SUCCEEDED,
        ANY,
    )
    m_notification_client.notify_webhook.assert_awaited_once_with(
        webhook_url=f_processed_payment.props.webhook_url,
        payment_id=f_processed_payment.pk,
        status=PaymentStatus.SUCCEEDED,
        amount=f_processed_payment.props.amount,
        currency=f_processed_payment.props.currency,
        processed_at=f_processed_payment.props.processed_at,
    )


@pytest.mark.unit
@pytest.mark.asyncio(loop_scope="function")
async def test_completed_payment_skips_gateway(
    f_process_use_case: ProcessPaymentUseCase,
    f_processed_payment: PaymentEntity,
    m_payment_repository: Mock,
    m_payment_gateway: Mock,
    m_notification_client: Mock,
) -> None:
    m_payment_repository.get_by_id.return_value = f_processed_payment

    await f_process_use_case.execute(f_processed_payment.pk)

    m_payment_gateway.process.assert_not_awaited()
    m_payment_repository.set_result_or_get.assert_not_awaited()
    m_notification_client.notify_webhook.assert_awaited_once()


@pytest.mark.unit
@pytest.mark.asyncio(loop_scope="function")
async def test_missing_payment_raises(
    f_process_use_case: ProcessPaymentUseCase,
    m_payment_repository: Mock,
    m_notification_client: Mock,
) -> None:
    payment_id = uuid.uuid4()
    m_payment_repository.get_by_id.return_value = None

    with pytest.raises(PaymentNotFoundError):
        await f_process_use_case.execute(payment_id)

    m_notification_client.notify_webhook.assert_not_awaited()


@pytest.mark.unit
@pytest.mark.asyncio(loop_scope="function")
async def test_pending_conflict_raises(
    f_process_use_case: ProcessPaymentUseCase,
    f_payment: PaymentEntity,
    m_payment_repository: Mock,
    m_payment_gateway: Mock,
) -> None:
    m_payment_repository.get_by_id.return_value = f_payment
    m_payment_gateway.process.return_value = PaymentStatus.SUCCEEDED
    m_payment_repository.set_result_or_get.return_value = f_payment

    with pytest.raises(PaymentProcessingConflictError):
        await f_process_use_case.execute(f_payment.pk)
