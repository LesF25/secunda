from faststream.rabbit import Channel, RabbitBroker

from src.core.settings import settings


def create_rabbit_broker() -> RabbitBroker:
    return RabbitBroker(
        str(settings.rabbit.url),
        default_channel=Channel(
            publisher_confirms=True,
            on_return_raises=True,
        ),
    )
