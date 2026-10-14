import uvicorn
from fastapi import FastAPI
from pydantic import ValidationError
from starlette.middleware.cors import CORSMiddleware

from src.api.exception_handlers import validation_error_handler
from src.api.middleware import TraceIDMiddleware
from src.api.router import api_router
from src.core.logging import configure_logging

configure_logging(service_name='api')

app = FastAPI(title='Payments API')
app.include_router(api_router)
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)
app.add_middleware(TraceIDMiddleware)
app.add_exception_handler(
    exc_class_or_status_code=ValidationError,
    handler=validation_error_handler,
)


if __name__ == '__main__':
    uvicorn.run(
        app,
        host='0.0.0.0',
        port=8000,
        log_config=None,
    )
