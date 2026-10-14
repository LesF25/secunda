import uuid
from typing import Annotated

from fastapi import HTTPException, status
from fastapi.params import Header


def get_idempotency_key(
    idempotency_key: Annotated[
        str | None,
        Header(
            alias='Idempotency-Key',
            convert_underscores=False
        )
    ] = None,
) -> uuid.UUID:
    if not idempotency_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing 'Idempotency-Key' header."
        )

    try:
        return uuid.UUID(idempotency_key)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid 'Idempotency-Key' format. Expected a valid UUID."
        ) from None
