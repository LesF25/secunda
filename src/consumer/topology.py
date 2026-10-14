from abc import ABC, abstractmethod
from collections.abc import Iterable

from faststream.rabbit import RabbitBroker


class BaseTopology(ABC):
    @abstractmethod
    async def declare(self, broker: RabbitBroker) -> None: ...


class TopologyManager:
    def __init__(self, topologies: Iterable[BaseTopology]) -> None:
        self._topologies = tuple(topologies)

    async def declare_all(self, broker: RabbitBroker) -> None:
        for topology in self._topologies:
            await topology.declare(broker)
