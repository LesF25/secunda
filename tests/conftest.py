import os
import uuid
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from decimal import Decimal

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from src.payments.domain.entities.currency import Currency
from src.payments.domain.entities.payment import PaymentEntity, PaymentProperties
from src.payments.domain.entities.payment_status import PaymentStatus
from src.payments.application.dto import CreatePaymentDTO


@pytest.fixture(scope="session")
def test_database_url() -> str:
    url = os.getenv("TEST_DATABASE_URL")
    if not url:
        pytest.skip(
            "integration tests require a migrated PostgreSQL TEST_DATABASE_URL"
        )
    return url


@pytest_asyncio.fixture(loop_scope="function")
async def engine(test_database_url: str) -> AsyncIterator[AsyncEngine]:
    test_engine = create_async_engine(test_database_url, poolclass=NullPool)
    async with test_engine.connect() as connection:
        tables = await connection.execute(
            text(
                "SELECT to_regclass('public.payments'), "
                "to_regclass('public.outbox')"
            )
        )
        if any(table is None for table in tables.one()):
            await test_engine.dispose()
            pytest.fail("TEST_DATABASE_URL does not contain the migrated schema")

    try:
        yield test_engine
    finally:
        await test_engine.dispose()


@pytest.fixture
def session_factory(
    engine: AsyncEngine,
) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(
        bind=engine,
        expire_on_commit=False,
        autoflush=False,
    )


@pytest_asyncio.fixture(loop_scope="function")
async def db_session(
    request: pytest.FixtureRequest,
    engine: AsyncEngine,
) -> AsyncIterator[AsyncSession]:
    if request.node.get_closest_marker("transactional_db") is None:
        pytest.fail("tests using db_session must be marked transactional_db")

    async with engine.connect() as connection:
        transaction = await connection.begin()
        factory = async_sessionmaker(
            bind=connection,
            expire_on_commit=False,
            autoflush=False,
            join_transaction_mode="create_savepoint",
        )
        try:
            async with factory() as session:
                yield session
        finally:
            if transaction.is_active:
                await transaction.rollback()


@pytest.fixture
def f_payment() -> PaymentEntity:
    return PaymentEntity(
        pk=uuid.uuid4(),
        props=PaymentProperties(
            idempotency_key=uuid.uuid4(),
            amount=Decimal("1250.50"),
            currency=Currency.RUB,
            description="Order 42",
            webhook_url="https://merchant.test/payment-hook",
            meta_data={"order_id": "order-42"},
            status=PaymentStatus.PENDING,
            created_at=datetime(2026, 10, 13, 8, 30, tzinfo=UTC),
        ),
    )


@pytest.fixture
def f_create_payment_dto(f_payment: PaymentEntity) -> CreatePaymentDTO:
    props = f_payment.props
    return CreatePaymentDTO(
        idempotency_key=props.idempotency_key,
        amount=props.amount,
        currency=props.currency,
        description=props.description,
        webhook_url=props.webhook_url,
        meta_data=props.meta_data,
    )
