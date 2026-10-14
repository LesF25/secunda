from unittest.mock import AsyncMock, Mock

import pytest
from faststream.rabbit import RabbitMessage

from src.consumer.payments.declarations import payments_retry_queues
from src.consumer.payments.publisher import (
    PaymentPublisher,
    PaymentRetryPublisher,
)


@pytest.fixture
def m_payment_publisher() -> Mock:
    publisher = Mock(spec=PaymentPublisher)
    publisher.publish_event = AsyncMock()
    return publisher


@pytest.fixture
def m_rabbit_message() -> Mock:
    message = Mock(spec=RabbitMessage)
    message.headers = {"source": "outbox"}
    message.message_id = "message-42"
    message.decode = AsyncMock(return_value={"payment_id": "payment-42"})
    return message


@pytest.fixture
def f_retry_publisher(m_payment_publisher: Mock) -> PaymentRetryPublisher:
    return PaymentRetryPublisher(m_payment_publisher, payments_retry_queues)


@pytest.fixture
def f_network_error() -> ConnectionError:
    return ConnectionError("offline")


@pytest.mark.unit
@pytest.mark.asyncio(loop_scope="function")
async def test_first_failure_schedules_retry(
    f_retry_publisher: PaymentRetryPublisher,
    f_network_error: ConnectionError,
    m_rabbit_message: Mock,
    m_payment_publisher: Mock,
) -> None:
    scheduled = await f_retry_publisher.publish_with_retry(
        m_rabbit_message,
        f_network_error,
    )

    assert scheduled is True
    m_payment_publisher.publish_event.assert_awaited_once_with(
        queue_name=payments_retry_queues[0].name,
        payload={"payment_id": "payment-42"},
        message_id="message-42",
        headers={"source": "outbox", "x-retry-attempt": 2},
    )


@pytest.mark.unit
@pytest.mark.asyncio(loop_scope="function")
async def test_last_failure_stops_retry(
    f_retry_publisher: PaymentRetryPublisher,
    f_network_error: ConnectionError,
    m_rabbit_message: Mock,
    m_payment_publisher: Mock,
) -> None:
    m_rabbit_message.headers = {"x-retry-attempt": 3}

    scheduled = await f_retry_publisher.publish_with_retry(
        m_rabbit_message,
        f_network_error,
    )

    assert scheduled is False
    m_payment_publisher.publish_event.assert_not_awaited()
