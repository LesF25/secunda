import uuid
from collections.abc import AsyncIterator

import pytest
import pytest_asyncio
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.outbox.infrastructure.models import OutboxMessage
from src.outbox.infrastructure.repositories.outbox_dispatch_repository import (
    OutboxDispatchRepository,
)


@pytest_asyncio.fixture(loop_scope="function")
async def f_outbox_rows(
    session_factory: async_sessionmaker[AsyncSession],
) -> AsyncIterator[tuple[OutboxMessage, ...]]:
    rows = tuple(
        OutboxMessage(
            queue_name="payments.new",
            payload={"payment_id": str(uuid.uuid4())},
        )
        for _ in range(4)
    )
    async with session_factory() as session:
        session.add_all(rows)
        await session.commit()

    try:
        yield rows
    finally:
        async with session_factory() as session:
            await session.execute(
                delete(OutboxMessage).where(
                    OutboxMessage.id.in_(row.id for row in rows)
                )
            )
            await session.commit()


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="function")
async def test_workers_lock_disjoint_batches(
    session_factory: async_sessionmaker[AsyncSession],
    f_outbox_rows: tuple[OutboxMessage, ...],
) -> None:
    first_token = uuid.uuid4()
    second_token = uuid.uuid4()

    async with (
        session_factory() as first_session,
        session_factory() as second_session,
    ):
        first_batch = await OutboxDispatchRepository(first_session).lock_batch(
            2,
            first_token,
        )
        second_batch = await OutboxDispatchRepository(second_session).lock_batch(
            4,
            second_token,
        )
        await first_session.commit()
        await second_session.commit()

    first_ids = {message.pk for message in first_batch}
    second_ids = {message.pk for message in second_batch}
    expected_ids = {row.id for row in f_outbox_rows}
    assert first_ids.isdisjoint(second_ids)
    assert first_ids | second_ids == expected_ids

    async with session_factory() as observer:
        locked_rows = (
            await observer.execute(
                select(
                    OutboxMessage.id,
                    OutboxMessage.lock_token,
                    OutboxMessage.lock_expires_at,
                ).where(OutboxMessage.id.in_(expected_ids))
            )
        ).all()

    token_by_id = {row.id: row.lock_token for row in locked_rows}
    assert {token_by_id[row_id] for row_id in first_ids} == {first_token}
    assert {token_by_id[row_id] for row_id in second_ids} == {second_token}


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="function")
async def test_delete_respects_lock_token(
    session_factory: async_sessionmaker[AsyncSession],
    f_outbox_rows: tuple[OutboxMessage, ...],
) -> None:
    owner_token = uuid.uuid4()
    foreign_token = uuid.uuid4()
    owner_ids = tuple(row.id for row in f_outbox_rows[:2])
    foreign_ids = tuple(row.id for row in f_outbox_rows[2:])
    all_ids = owner_ids + foreign_ids

    async with session_factory() as session:
        await session.execute(
            update(OutboxMessage)
            .where(OutboxMessage.id.in_(owner_ids))
            .values(lock_token=owner_token)
        )
        await session.execute(
            update(OutboxMessage)
            .where(OutboxMessage.id.in_(foreign_ids))
            .values(lock_token=foreign_token)
        )
        await session.commit()

    async with session_factory() as session:
        repository = OutboxDispatchRepository(session)
        await repository.delete_published(owner_token, all_ids)
        await session.commit()

    async with session_factory() as observer:
        remaining_ids = set(
            await observer.scalars(
                select(OutboxMessage.id).where(
                    OutboxMessage.id.in_(all_ids)
                )
            )
        )
    assert remaining_ids == set(foreign_ids)
