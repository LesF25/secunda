from fastapi import APIRouter

from src.payments.api.v1.payments import payment_router


v1_router = APIRouter(prefix='/v1')
v1_router.include_router(payment_router)
