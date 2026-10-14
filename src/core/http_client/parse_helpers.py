from typing import Any

from aiohttp import ClientResponse


class UnknownError(Exception): ...


async def response_to_json(response: ClientResponse) -> Any:
    try:
        return await response.json()
    except ValueError as exc:
        response_text = await response.text()
        raise UnknownError(f'Bad json: {response_text}') from exc
