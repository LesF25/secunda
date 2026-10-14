from src.core.application.transactions import SessionManagerProtocol
from src.outbox.domain.entities.outbox_message import OutboxMessageEntity
from src.outbox.domain.repositories.outbox import OutboxRepositoryProtocol
from src.payments.application.dto import CreatePaymentDTO
from src.payments.application.queues import PaymentQueue
from src.payments.domain.entities.payment import PaymentEntity
from src.payments.domain.entities.payment_status import PaymentStatus
from src.payments.domain.events.payments import PaymentCreatedEvent
from src.payments.domain.repositories.payment import PaymentRepositoryProtocol


class CreatePaymentUseCase:
    def __init__(
        self,
        session_manager: SessionManagerProtocol,
        payment_repository: PaymentRepositoryProtocol,
        outbox_repository: OutboxRepositoryProtocol,
    ) -> None:
        self._session_manager = session_manager
        self._payments_repo = payment_repository
        self._outbox_repo = outbox_repository

    async def execute(self, dto: CreatePaymentDTO) -> PaymentEntity:
        candidate = PaymentEntity.create(
            amount=dto.amount,
            currency=dto.currency,
            description=dto.description,
            webhook_url=dto.webhook_url,
            meta_data=dto.meta_data,
            status=PaymentStatus.PENDING,
            idempotency_key=dto.idempotency_key,
        )

        async with self._session_manager:
            payment, created = await self._payments_repo.create_or_get(candidate)

            if created:
                event = PaymentCreatedEvent(payment_id=payment.pk)
                outbox = OutboxMessageEntity.create(
                    queue_name=PaymentQueue.NEW.value,
                    payload=event.to_dict(),
                )
                await self._outbox_repo.create(outbox)

        return payment
