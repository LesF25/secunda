import asyncio
import random
import uuid

from src.payments.domain.entities.payment_status import PaymentStatus


class SimulatedPaymentGateway:
    def __init__(self) -> None:
        self._results: dict[tuple[uuid.UUID, str], PaymentStatus] = {}

    async def process(
        self,
        payment_id: uuid.UUID,
        idempotency_key: str,
    ) -> PaymentStatus:
        request_key = payment_id, idempotency_key
        if result := self._results.get(request_key):
            return result

        await asyncio.sleep(random.uniform(2, 5))
        result = (
            PaymentStatus.SUCCEEDED
            if random.random() < 0.9
            else PaymentStatus.FAILED
        )
        return self._results.setdefault(request_key, result)
