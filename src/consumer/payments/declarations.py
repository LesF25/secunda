from faststream.rabbit import ExchangeType, RabbitExchange, RabbitQueue

from src.payments.application.queues import PaymentQueue


payments_dlx = RabbitExchange(
    'payments.dlx',
    type=ExchangeType.DIRECT,
    durable=True,
)

payments_dlq = RabbitQueue(
    'payments.new.dlq',
    durable=True,
)

payments_queue = RabbitQueue(
    PaymentQueue.NEW.value,
    durable=True,
    arguments={
        'x-dead-letter-exchange': payments_dlx.name,
        'x-dead-letter-routing-key': PaymentQueue.NEW.value,
        'x-single-active-consumer': True,
    },
)

payments_retry_queues = (
    RabbitQueue(
        'payments.new.retry.1',
        durable=True,
        arguments={
            'x-message-ttl': 2_000,
            'x-dead-letter-exchange': '',
            'x-dead-letter-routing-key': PaymentQueue.NEW.value,
        },
    ),
    RabbitQueue(
        'payments.new.retry.2',
        durable=True,
        arguments={
            'x-message-ttl': 4_000,
            'x-dead-letter-exchange': '',
            'x-dead-letter-routing-key': PaymentQueue.NEW.value,
        },
    ),
)
