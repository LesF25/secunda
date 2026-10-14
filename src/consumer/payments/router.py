from typing import Annotated

from faststream import AckPolicy, Depends
from faststream.rabbit import Channel, RabbitRouter

from src.consumer.payments.declarations import payments_queue
from src.consumer.payments.dependencies import get_process_payment_use_case
from src.consumer.payments.middleware import RetryMiddleware
from src.consumer.payments.schemas import PaymentCreatedMessage
from src.payments.application.use_cases.process_payment import (
    ProcessPaymentUseCase,
)

router = RabbitRouter(middlewares=(RetryMiddleware,))


@router.subscriber(
    payments_queue,
    channel=Channel(prefetch_count=1),
    ack_policy=AckPolicy.MANUAL,
)
async def process_payment(
    event: PaymentCreatedMessage,
    use_case: Annotated[
        ProcessPaymentUseCase,
        Depends(get_process_payment_use_case),
    ],
) -> None:
    await use_case.execute(event.payment_id)
