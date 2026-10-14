from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from faststream.annotations import ContextRepo

from src.outbox.broker import broker
from src.outbox.scheduler import scheduler


@asynccontextmanager
async def lifespan(_: ContextRepo) -> AsyncIterator[None]:
    async with broker:
        scheduler.start()
        try:
            yield
        finally:
            scheduler.shutdown(wait=False)
