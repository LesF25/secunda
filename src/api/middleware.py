import uuid

import structlog
from fastapi import Request, Response
from starlette.middleware.base import (
    BaseHTTPMiddleware,
    RequestResponseEndpoint,
)

TRACE_ID_HEADER = 'x-im-trace-id'


class TraceIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        trace_id = request.headers.get(TRACE_ID_HEADER, str(uuid.uuid4()))

        with structlog.contextvars.bound_contextvars(trace_id=trace_id):
            response = await call_next(request)

        response.headers[TRACE_ID_HEADER] = trace_id
        return response
