import uuid
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PaymentCreatedEvent:
    payment_id: uuid.UUID

    def to_dict(self) -> dict[str, str]:
        return {'payment_id': str(self.payment_id)}
