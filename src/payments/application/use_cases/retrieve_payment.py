from src.payments.application.dto import RetrievePaymentDTO
from src.payments.domain.entities.payment import PaymentEntity
from src.payments.domain.repositories.payment import PaymentRepositoryProtocol


class RetrievePaymentUseCase:
    def __init__(
        self,
        payment_repository: PaymentRepositoryProtocol,
    ) -> None:
        self._payments = payment_repository

    async def execute(self, dto: RetrievePaymentDTO) -> PaymentEntity | None:
        return await self._payments.get_by_id(dto.payment_id)
