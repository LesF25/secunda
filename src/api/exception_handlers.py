from fastapi import Request, Response
from fastapi.encoders import jsonable_encoder
from pydantic import ValidationError
from starlette.responses import JSONResponse


async def validation_error_handler(
    _: Request,
    exc: ValidationError,
) -> Response:
    return JSONResponse(
        status_code=422,
        content={'detail': jsonable_encoder(exc.errors())},
    )
