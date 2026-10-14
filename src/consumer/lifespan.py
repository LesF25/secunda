from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import aiohttp
from faststream.annotations import ContextRepo

from src.consumer.broker import broker
from src.consumer.payments import payments_topology
from src.consumer.topology import TopologyManager
from src.core.settings import settings

topology_manager = TopologyManager((payments_topology,))


@asynccontextmanager
async def lifespan(context: ContextRepo) -> AsyncIterator[None]:
    async with broker:
        await topology_manager.declare_all(broker)
        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(
                total=settings.webhook.timeout_seconds,
            )
        ) as http_session:
            context.set_global('http_session', http_session)
            try:
                yield
            finally:
                context.reset_global('http_session')
