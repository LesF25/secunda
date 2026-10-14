from fastapi import APIRouter, Depends

from src.api.security import require_api_key
from src.payments.api.v1.router import v1_router

api_router = APIRouter(
    prefix='/api',
    dependencies=[Depends(require_api_key)],
)
api_router.include_router(v1_router)
