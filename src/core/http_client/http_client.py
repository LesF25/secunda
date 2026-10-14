import logging
from collections.abc import Callable
from typing import Any, Awaitable

import aiohttp

from .exception_handling import DefaultExceptionHandler, ExceptionHandler


class HttpClient:
    def __init__(
        self,
        session: aiohttp.ClientSession,
        response_handler: Callable[[aiohttp.ClientResponse], Awaitable[Any]],
        exception_handler: type[ExceptionHandler] | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        self._session = session
        self._response_handler = response_handler
        self._logger = logger or logging.getLogger(__name__)

        exception_handler_type = exception_handler or DefaultExceptionHandler
        self._exception_handler = exception_handler_type(self._logger)

    async def request(
        self,
        method: str,
        url: str,
        auth: aiohttp.BasicAuth | None = None,
        params: dict[str, Any] | None = None,
        data: aiohttp.FormData | dict[str, Any] | str | bytes | None = None,
        json: dict[str, Any] | None = None,
        headers: dict[str, Any] | None = None,
        cookies: dict[str, Any] | None = None,
        timeout: aiohttp.ClientTimeout | None = None,
    ) -> Any:
        try:
            response = await self._session.request(
                method=method,
                url=url,
                auth=auth,
                headers=headers,
                params=params,
                data=data,
                json=json,
                cookies=cookies,
                timeout=timeout,
            )
        except Exception as e:
            self._exception_handler(e)
            raise

        async with response:
            return await self._response_handler(response)
