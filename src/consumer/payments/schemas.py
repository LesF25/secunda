import uuid

from pydantic import BaseModel


class PaymentCreatedMessage(BaseModel):
    payment_id: uuid.UUID
