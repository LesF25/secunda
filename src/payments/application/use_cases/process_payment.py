import uuid
from datetime import datetime, timezone

from src.core.application.transactions import SessionManagerProtocol
from src.payments.application.interfaces import (
    NotificationClientProtocol,
    PaymentGatewayProtocol,
)
from src.payments.domain.entities.payment import PaymentEntity
from src.payments.domain.entities.payment_status import PaymentStatus
from src.payments.domain.repositories.payment import PaymentRepositoryProtocol


class PaymentNotFoundError(Exception):
    pass


class PaymentProcessingConflictError(Exception):
    pass


class ProcessPaymentUseCase:
    def __init__(
        self,
        payment_repository: PaymentRepositoryProtocol,
        session_manager: SessionManagerProtocol,
        payment_gateway: PaymentGatewayProtocol,
        notification_client: NotificationClientProtocol,
    ) -> None:
        self._payment_repository = payment_repository
        self._session_manager = session_manager
        self._payment_gateway = payment_gateway
        self._notification_client = notification_client

    async def execute(self, payment_id: uuid.UUID) -> None:
        payment = await self._get_payment(payment_id)
        resolved = await self._resolve_payment_status(payment)

        await self._notification_client.notify_webhook(
            webhook_url=resolved.props.webhook_url,
            payment_id=resolved.pk,
            status=resolved.props.status,
            amount=resolved.props.amount,
            currency=resolved.props.currency,
            processed_at=resolved.props.processed_at,
        )

    async def _get_payment(self, payment_id: uuid.UUID) -> PaymentEntity:
        async with self._session_manager:
            payment = await self._payment_repository.get_by_id(payment_id)

        if payment is None:
            raise PaymentNotFoundError(str(payment_id))

        return payment

    async def _resolve_payment_status(
        self,
        payment: PaymentEntity,
    ) -> PaymentEntity:
        if payment.props.status is not PaymentStatus.PENDING:
            return payment

        payment_id = payment.pk
        result_status = await self._payment_gateway.process(
            payment_id=payment_id,
            idempotency_key=str(payment_id),
        )
        return await self._save_payment_result(
            payment_id,
            result_status,
            datetime.now(timezone.utc),
        )

    async def _save_payment_result(
        self,
        payment_id: uuid.UUID,
        result_status: PaymentStatus,
        processed_at: datetime,
    ) -> PaymentEntity:
        async with self._session_manager:
            payment = await self._payment_repository.set_result_or_get(
                payment_id,
                result_status,
                processed_at,
            )

        if payment is None:
            raise PaymentNotFoundError(str(payment_id))

        if payment.props.status.is_terminal:
            return payment

        raise PaymentProcessingConflictError(str(payment_id))
