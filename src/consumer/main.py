from faststream import FastStream

from src.consumer.broker import broker
from src.consumer.lifespan import lifespan
from src.consumer.payments.router import router as payments_router
from src.core.logging import configure_logging

configure_logging(service_name='consumer')

broker.include_router(payments_router)

app = FastStream(broker, lifespan=lifespan)
