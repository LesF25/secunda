import asyncio

import pytest
from sqlalchemy import event, func, select, text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from src.core.infrastructure.session_managers import TransactionSessionManager
from src.outbox.infrastructure.models import OutboxMessage
from src.outbox.infrastructure.repositories.outbox_message_repository import (
    OutboxRepository,
)
from src.payments.application.dto import CreatePaymentDTO
from src.payments.application.use_cases.create_payment import (
    CreatePaymentUseCase,
)
from src.payments.infrastructure.models import Payment
from src.payments.infrastructure.repositories.payment_repository import (
    PaymentRepository,
)


@pytest.fixture
def f_create_use_case(db_session: AsyncSession) -> CreatePaymentUseCase:
    return CreatePaymentUseCase(
        session_manager=TransactionSessionManager(db_session),
        payment_repository=PaymentRepository(db_session),
        outbox_repository=OutboxRepository(db_session),
    )


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="function")
@pytest.mark.transactional_db
async def test_create_persists_event(
    f_create_use_case: CreatePaymentUseCase,
    f_create_payment_dto: CreatePaymentDTO,
    db_session: AsyncSession,
) -> None:
    payment = await f_create_use_case.execute(f_create_payment_dto)

    stored_payment = await db_session.scalar(
        select(Payment).where(Payment.id == payment.pk)
    )
    stored_event = await db_session.scalar(
        select(OutboxMessage).where(
            OutboxMessage.payload["payment_id"].astext == str(payment.pk)
        )
    )
    assert stored_payment is not None
    assert stored_event is not None
    assert stored_event.queue_name == "payments.new"


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="function")
@pytest.mark.transactional_db
async def test_duplicate_reuses_payment(
    f_create_use_case: CreatePaymentUseCase,
    f_create_payment_dto: CreatePaymentDTO,
    db_session: AsyncSession,
) -> None:
    first = await f_create_use_case.execute(f_create_payment_dto)
    second = await f_create_use_case.execute(f_create_payment_dto)

    payment_count = await db_session.scalar(
        select(func.count()).select_from(Payment).where(
            Payment.idempotency_key == f_create_payment_dto.idempotency_key
        )
    )
    event_count = await db_session.scalar(
        select(func.count()).select_from(OutboxMessage).where(
            OutboxMessage.payload["payment_id"].astext == str(first.pk)
        )
    )
    assert second.pk == first.pk
    assert payment_count == 1
    assert event_count == 1


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="function")
async def test_cancelled_create_rolls_back(
    engine: AsyncEngine,
    session_factory: async_sessionmaker[AsyncSession],
    f_create_payment_dto: CreatePaymentDTO,
) -> None:
    insert_started = asyncio.Event()

    def observe_outbox_insert(
        _connection,
        _cursor,
        statement: str,
        _parameters,
        _context,
        _executemany,
    ) -> None:
        if statement.lstrip().upper().startswith("INSERT INTO OUTBOX"):
            insert_started.set()

    event.listen(
        engine.sync_engine,
        "before_cursor_execute",
        observe_outbox_insert,
    )
    try:
        async with (
            session_factory() as blocker,
            session_factory() as worker,
        ):
            await blocker.execute(
                text("LOCK TABLE outbox IN ACCESS EXCLUSIVE MODE")
            )
            use_case = CreatePaymentUseCase(
                session_manager=TransactionSessionManager(worker),
                payment_repository=PaymentRepository(worker),
                outbox_repository=OutboxRepository(worker),
            )
            task = asyncio.create_task(
                use_case.execute(f_create_payment_dto)
            )
            try:
                await asyncio.wait_for(insert_started.wait(), timeout=2)
                task.cancel()

                with pytest.raises(asyncio.CancelledError):
                    await task

                assert not worker.in_transaction()
            finally:
                if not task.done():
                    task.cancel()
                    await asyncio.gather(task, return_exceptions=True)
                await blocker.rollback()
    finally:
        event.remove(
            engine.sync_engine,
            "before_cursor_execute",
            observe_outbox_insert,
        )

    async with session_factory() as observer:
        payment = await observer.scalar(
            select(Payment).where(
                Payment.idempotency_key == f_create_payment_dto.idempotency_key
            )
        )
    assert payment is None
