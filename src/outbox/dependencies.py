from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from src.outbox.application.use_cases.dispatch_outbox import OutboxDispatcher
from src.core.infrastructure.connection import session_factory
from src.core.infrastructure.session_managers import SessionManager
from src.outbox.broker import broker
from src.outbox.infrastructure.repositories.outbox_dispatch_repository import (
    OutboxDispatchRepository,
)
from src.outbox.transport.publisher import OutboxPublisher


@asynccontextmanager
async def get_outbox_dispatcher() -> AsyncIterator[OutboxDispatcher]:
    async with session_factory() as session:
        yield OutboxDispatcher(
            repository=OutboxDispatchRepository(session),
            session_manager=SessionManager(session),
            publisher=OutboxPublisher(broker),
        )
