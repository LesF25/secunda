from faststream.rabbit import RabbitBroker

from src.consumer.payments.declarations import (
    payments_dlq,
    payments_dlx,
    payments_queue,
    payments_retry_queues,
)
from src.consumer.topology import BaseTopology
from src.payments.application.queues import PaymentQueue


class PaymentsTopology(BaseTopology):
    async def declare(self, broker: RabbitBroker) -> None:
        dlx = await broker.declare_exchange(payments_dlx)
        await broker.declare_queue(payments_queue)

        for retry_queue in payments_retry_queues:
            await broker.declare_queue(retry_queue)

        dlq = await broker.declare_queue(payments_dlq)
        await dlq.bind(
            exchange=dlx,
            routing_key=PaymentQueue.NEW.value,
        )


payments_topology = PaymentsTopology()
