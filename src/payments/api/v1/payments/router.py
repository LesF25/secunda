import uuid
from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.params import Body

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
from src.payments.api.v1.dependencies import get_idempotency_key
from src.payments.api.v1.payments.dependencies import (
    get_create_payment_use_case,
    get_retrieve_payment_use_case,
)
from src.payments.api.v1.payments.schemas import (
    PaymentDetailResponse,
    PaymentRequest,
    PaymentResponse,
)

logger = structlog.getLogger(__name__)

payment_router = APIRouter(prefix='/payments')


@payment_router.post(
    path='',
    status_code=status.HTTP_202_ACCEPTED,
)
async def create_payment(
    data: Annotated[PaymentRequest, Body()],
    idempotency_key: Annotated[
        uuid.UUID,
        Depends(get_idempotency_key),
    ],
    use_case: Annotated[
        CreatePaymentUseCase, Depends(get_create_payment_use_case),
    ],
) -> PaymentResponse:
    dto = CreatePaymentDTO(
        idempotency_key=idempotency_key,
        amount=data.amount,
        currency=data.currency,
        description=data.description,
        webhook_url=str(data.webhook_url),
        meta_data=data.meta_data,
    )
    payment = await use_case.execute(dto)

    return PaymentResponse.from_entity(payment)


@payment_router.get(
    path='/{payment_id}',
    status_code=status.HTTP_200_OK,
)
async def payment_detail(
    payment_id: uuid.UUID,
    use_case: Annotated[
        RetrievePaymentUseCase,
        Depends(get_retrieve_payment_use_case),
    ],
) -> PaymentDetailResponse:
    dto = RetrievePaymentDTO(payment_id=payment_id)
    payment = await use_case.execute(dto)

    if payment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Payment not found',
        )

    return PaymentDetailResponse.from_entity(payment)
