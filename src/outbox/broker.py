from faststream.rabbit import RabbitBroker

from src.core.infrastructure.rabbit import create_rabbit_broker


broker: RabbitBroker = create_rabbit_broker()
