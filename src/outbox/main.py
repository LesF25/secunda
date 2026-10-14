from faststream import FastStream

from src.core.logging import configure_logging
from src.outbox.broker import broker
from src.outbox.lifespan import lifespan

configure_logging(service_name='outbox')

app = FastStream(broker, lifespan=lifespan)
