from unittest.mock import AsyncMock, MagicMock, Mock

import pytest

from src.core.application.transactions import SessionManagerProtocol
from src.payments.domain.repositories.payment import PaymentRepositoryProtocol


@pytest.fixture
def m_session_manager() -> MagicMock:
    manager = MagicMock(spec=SessionManagerProtocol)
    manager.__aenter__ = AsyncMock(return_value=manager)
    manager.__aexit__ = AsyncMock(return_value=None)
    return manager


@pytest.fixture
def m_payment_repository() -> Mock:
    repository = Mock(spec=PaymentRepositoryProtocol)
    repository.create_or_get = AsyncMock()
    repository.get_by_id = AsyncMock()
    repository.set_result_or_get = AsyncMock()
    return repository
