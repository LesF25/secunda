import asyncio
import logging

import aiohttp

from src.core.http_client.exceptions import HttpRetryException


class ExceptionHandler:
    def __init__(self, logger: logging.Logger) -> None:
        self._logger = logger

    def __call__(self, exc: Exception) -> None:
        raise NotImplementedError


class DefaultExceptionHandler(ExceptionHandler):
    EXPECTED_REQUEST_EXCEPTIONS = (
        aiohttp.ClientConnectionError,
        aiohttp.ClientPayloadError,
        aiohttp.ClientSSLError,
        aiohttp.ServerTimeoutError,
        asyncio.TimeoutError,
    )

    def __call__(self, exc: Exception) -> None:
        if isinstance(exc, aiohttp.ClientError | asyncio.TimeoutError):
            self._raise_retry_error(exc)

        self._logger.warning(
            'Unexpected exception: request_exception_class=%s, request_exception=%s',
            exc.__class__.__name__,
            str(exc),
        )
        raise exc

    def _raise_retry_error(
        self,
        exc: aiohttp.ClientError | asyncio.TimeoutError,
    ) -> None:
        if not isinstance(exc, self.EXPECTED_REQUEST_EXCEPTIONS):
            self._logger.warning(
                'Unexpected request exception: request_exception_class=%s, request_exception=%s',
                exc.__class__.__name__,
                str(exc),
            )

        message = (
            'Request exception: '
            f'request_exception_class={exc.__class__.__name__}, '
            f'request_exception={exc}'
        )
        self._logger.warning(message)
        raise HttpRetryException(message) from exc
