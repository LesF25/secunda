import uuid
from collections.abc import AsyncIterator, Callable, Iterator
from unittest.mock import AsyncMock, Mock

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from src.api.main import app as payments_app
from src.payments.application.dto import (
    CreatePaymentDTO,
    RetrievePaymentDTO,
)
from src.payments.application.use_cases.create_payment import (
    CreatePaymentUseCase,
)
from src.payments.application.use_cases.retrieve_payment import (
    RetrievePaymentUseCase,
)
from src.payments.api.v1.payments.dependencies import (
    get_create_payment_use_case,
    get_retrieve_payment_use_case,
)
from src.payments.domain.entities.payment import PaymentEntity


@pytest.fixture
def api_app() -> Iterator[FastAPI]:
    payments_app.dependency_overrides.clear()
    try:
        yield payments_app
    finally:
        payments_app.dependency_overrides.clear()


@pytest_asyncio.fixture(loop_scope="function")
async def api_client(api_app: FastAPI) -> AsyncIterator[AsyncClient]:
    transport = ASGITransport(app=api_app)
    async with AsyncClient(
        transport=transport,
        base_url="http://testserver",
    ) as client:
        yield client


@pytest.fixture
def f_auth_headers(f_payment: PaymentEntity) -> dict[str, str]:
    return {
        "X-API-Key": "development-secret",
        "Idempotency-Key": str(f_payment.props.idempotency_key),
    }


@pytest.fixture
def override_dependency(
    api_app: FastAPI,
) -> Iterator[Callable[[Callable, object], None]]:
    overridden: list[Callable] = []

    def apply(original: Callable, replacement: object) -> None:
        api_app.dependency_overrides[original] = lambda: replacement
        overridden.append(original)

    yield apply

    for original in overridden:
        api_app.dependency_overrides.pop(original, None)


@pytest.mark.e2e
@pytest.mark.asyncio(loop_scope="function")
async def test_create_calls_use_case(
    api_client: AsyncClient,
    f_auth_headers: dict[str, str],
    f_payment: PaymentEntity,
    f_create_payment_dto: CreatePaymentDTO,
    override_dependency: Callable[[Callable, object], None],
) -> None:
    m_use_case = Mock(spec=CreatePaymentUseCase)
    m_use_case.execute = AsyncMock(return_value=f_payment)
    override_dependency(get_create_payment_use_case, m_use_case)
    payload = {
        "amount": str(f_create_payment_dto.amount),
        "currency": f_create_payment_dto.currency.value,
        "description": f_create_payment_dto.description,
        "webhook_url": f_create_payment_dto.webhook_url,
        "meta_data": f_create_payment_dto.meta_data,
    }

    response = await api_client.post(
        "/api/v1/payments",
        json=payload,
        headers=f_auth_headers,
    )

    assert response.status_code == 202
    assert response.json() == {
        "payment_id": str(f_payment.pk),
        "status": "pending",
        "created_at": "2026-10-13T08:30:00Z",
    }
    m_use_case.execute.assert_awaited_once_with(f_create_payment_dto)


@pytest.mark.e2e
@pytest.mark.asyncio(loop_scope="function")
async def test_detail_calls_use_case(
    api_client: AsyncClient,
    f_auth_headers: dict[str, str],
    f_payment: PaymentEntity,
    override_dependency: Callable[[Callable, object], None],
) -> None:
    m_use_case = Mock(spec=RetrievePaymentUseCase)
    m_use_case.execute = AsyncMock(return_value=f_payment)
    override_dependency(get_retrieve_payment_use_case, m_use_case)

    response = await api_client.get(
        f"/api/v1/payments/{f_payment.pk}",
        headers=f_auth_headers,
    )

    assert response.status_code == 200
    assert response.json()["payment_id"] == str(f_payment.pk)
    assert response.json()["amount"] == "1250.50"
    m_use_case.execute.assert_awaited_once_with(
        RetrievePaymentDTO(payment_id=f_payment.pk)
    )


@pytest.mark.e2e
@pytest.mark.asyncio(loop_scope="function")
async def test_missing_detail_returns_not_found(
    api_client: AsyncClient,
    f_auth_headers: dict[str, str],
    override_dependency: Callable[[Callable, object], None],
) -> None:
    payment_id = uuid.uuid4()
    m_use_case = Mock(spec=RetrievePaymentUseCase)
    m_use_case.execute = AsyncMock(return_value=None)
    override_dependency(get_retrieve_payment_use_case, m_use_case)

    response = await api_client.get(
        f"/api/v1/payments/{payment_id}",
        headers=f_auth_headers,
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Payment not found"}
    m_use_case.execute.assert_awaited_once_with(
        RetrievePaymentDTO(payment_id=payment_id)
    )
