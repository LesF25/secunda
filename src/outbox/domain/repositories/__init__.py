"""Repository contracts required by the outbox domain."""

from src.outbox.domain.repositories.outbox import (
    OutboxDispatchRepositoryProtocol,
    OutboxRepositoryProtocol,
)

__all__ = (
    'OutboxDispatchRepositoryProtocol',
    'OutboxRepositoryProtocol',
)
