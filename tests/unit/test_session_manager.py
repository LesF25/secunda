import asyncio
from unittest.mock import AsyncMock, Mock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.infrastructure.session_managers import TransactionSessionManager


@pytest.fixture
def m_db_session() -> Mock:
    session = Mock(spec=AsyncSession)
    session.in_transaction.return_value = False
    session.begin = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()

    return session


@pytest.mark.unit
@pytest.mark.asyncio(loop_scope="function")
async def test_cancellation_rolls_back(m_db_session: Mock) -> None:
    manager = TransactionSessionManager(m_db_session)

    with pytest.raises(asyncio.CancelledError):
        async with manager:
            raise asyncio.CancelledError

    m_db_session.begin.assert_awaited_once()
    m_db_session.rollback.assert_awaited_once()
    m_db_session.commit.assert_not_awaited()
