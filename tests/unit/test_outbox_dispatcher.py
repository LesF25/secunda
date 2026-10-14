import asyncio
import uuid
from unittest.mock import AsyncMock, MagicMock, Mock

import pytest

from src.outbox.application.interfaces import OutboxPublisherProtocol
from src.outbox.application.use_cases.dispatch_outbox import OutboxDispatcher
from src.outbox.domain.entities.outbox_message import OutboxMessageEntity
from src.outbox.domain.repositories.outbox import (
    OutboxDispatchRepositoryProtocol,
)


@pytest.fixture
def m_dispatch_repository() -> Mock:
    repository = Mock(spec=OutboxDispatchRepositoryProtocol)
    repository.lock_batch = AsyncMock()
    repository.delete_published = AsyncMock()
    return repository


@pytest.fixture
def m_outbox_publisher() -> Mock:
    publisher = Mock(spec=OutboxPublisherProtocol)
    publisher.publish = AsyncMock()
    return publisher


@pytest.fixture
def f_outbox_batch() -> tuple[OutboxMessageEntity, OutboxMessageEntity]:
    return (
        OutboxMessageEntity.create(
            queue_name="payments.new",
            payload={"payment_id": str(uuid.uuid4())},
        ),
        OutboxMessageEntity.create(
            queue_name="payments.new",
            payload={"payment_id": str(uuid.uuid4())},
        ),
    )


@pytest.fixture
def f_dispatcher(
    m_dispatch_repository: Mock,
    m_session_manager: MagicMock,
    m_outbox_publisher: Mock,
) -> OutboxDispatcher:
    return OutboxDispatcher(
        repository=m_dispatch_repository,
        session_manager=m_session_manager,
        publisher=m_outbox_publisher,
    )


@pytest.mark.unit
@pytest.mark.asyncio(loop_scope="function")
async def test_partial_batch_deletes_successes(
    f_dispatcher: OutboxDispatcher,
    f_outbox_batch: tuple[OutboxMessageEntity, OutboxMessageEntity],
    m_dispatch_repository: Mock,
    m_outbox_publisher: Mock,
) -> None:
    m_dispatch_repository.lock_batch.return_value = list(f_outbox_batch)
    m_outbox_publisher.publish.side_effect = (None, ConnectionError("offline"))

    await f_dispatcher.dispatch_once()

    batch_size, lock_token = m_dispatch_repository.lock_batch.await_args.args
    delete_token, published_ids = (
        m_dispatch_repository.delete_published.await_args.args
    )
    assert batch_size == OutboxDispatcher.BATCH_SIZE
    assert delete_token == lock_token
    assert published_ids == (f_outbox_batch[0].pk,)


@pytest.mark.unit
@pytest.mark.asyncio(loop_scope="function")
async def test_cancelled_publish_propagates(
    f_dispatcher: OutboxDispatcher,
    f_outbox_batch: tuple[OutboxMessageEntity, OutboxMessageEntity],
    m_dispatch_repository: Mock,
    m_outbox_publisher: Mock,
) -> None:
    m_dispatch_repository.lock_batch.return_value = [f_outbox_batch[0]]
    m_outbox_publisher.publish.side_effect = asyncio.CancelledError

    with pytest.raises(asyncio.CancelledError):
        await f_dispatcher.dispatch_once()

    m_dispatch_repository.delete_published.assert_not_awaited()


@pytest.mark.unit
@pytest.mark.asyncio(loop_scope="function")
async def test_empty_batch_skips_publish(
    f_dispatcher: OutboxDispatcher,
    m_dispatch_repository: Mock,
    m_outbox_publisher: Mock,
) -> None:
    m_dispatch_repository.lock_batch.return_value = []

    await f_dispatcher.dispatch_once()

    m_outbox_publisher.publish.assert_not_awaited()
    m_dispatch_repository.delete_published.assert_not_awaited()
