from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.payments.domain.entities.payment import PaymentEntity
from src.payments.domain.entities.payment_status import PaymentStatus
from src.payments.infrastructure.repositories.payment_repository import (
    PaymentRepository,
)


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="function")
@pytest.mark.transactional_db
async def test_first_result_wins_race(
    db_session: AsyncSession,
    f_payment: PaymentEntity,
) -> None:
    repository = PaymentRepository(db_session)
    stored, _ = await repository.create_or_get(f_payment)
    first_time = datetime.now(UTC)

    first = await repository.set_result_or_get(
        stored.pk,
        PaymentStatus.SUCCEEDED,
        first_time,
    )
    second = await repository.set_result_or_get(
        stored.pk,
        PaymentStatus.FAILED,
        first_time + timedelta(seconds=1),
    )

    assert first is not None
    assert second is not None
    assert first.props.status is PaymentStatus.SUCCEEDED
    assert second.props.status is PaymentStatus.SUCCEEDED
    assert second.props.processed_at == first_time
