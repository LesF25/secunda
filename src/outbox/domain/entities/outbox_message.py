import uuid
from dataclasses import dataclass
from typing import Any

from src.core.domain.entities.entity import AggregateRoot


@dataclass(frozen=True, slots=True)
class OutboxMessageProperties:
    queue_name: str
    payload: dict[str, Any]


class OutboxMessageEntity(
    AggregateRoot[uuid.UUID, OutboxMessageProperties],
):
    @classmethod
    def create(
        cls,
        queue_name: str,
        payload: dict[str, Any],
    ) -> 'OutboxMessageEntity':
        return cls(
            pk=cls._get_entity_id(),
            props=OutboxMessageProperties(
                queue_name=queue_name,
                payload=payload,
            ),
        )
