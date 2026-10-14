import secrets
from typing import Annotated

from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader

from src.core.settings import settings

api_key_header = APIKeyHeader(
    name='X-API-Key',
    auto_error=False,
    scheme_name='ApiKeyAuth',
)


def require_api_key(
    api_key: Annotated[str | None, Security(api_key_header)],
) -> None:
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Invalid API key',
        )

    if not secrets.compare_digest(api_key, settings.app.api_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Invalid API key',
        )
