import dataclasses
import uuid
from dataclasses import asdict
from typing import Any, Generic, TypeVar

TEntityID = TypeVar('TEntityID')
TEntityProperties = TypeVar('TEntityProperties')


class Entity(Generic[TEntityID, TEntityProperties]):
    def __init__(
        self,
        pk: TEntityID | None,
        props: TEntityProperties
    ) -> None:
        assert dataclasses.is_dataclass(props)
        assert getattr(props, dataclasses._PARAMS).frozen

        self.__pk = pk
        self._props = props

    @property
    def pk(self) -> TEntityID:
        return self.__pk

    @property
    def props(self) -> TEntityProperties:
        return self._props

    def __eq__(
        self,
        other: Entity[TEntityID, TEntityProperties]
    ) -> bool:
        if not isinstance(other, self.__class__):
            return False

        return self.__pk == other.__pk

    def __hash__(self) -> int:
        return hash((self.__class__, self.__pk))

    def to_dict(self) -> dict[str, Any]:
        return {
            'id': self.pk,
            **asdict(self._props),
        }


class AggregateRoot(Entity[TEntityID, TEntityProperties]):
    @classmethod
    def _get_entity_id(cls) -> uuid.UUID:
        return uuid.uuid7()
