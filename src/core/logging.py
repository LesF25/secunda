import logging
from logging.handlers import RotatingFileHandler

import structlog

from src.core.settings import settings


def configure_logging(
    *,
    service_name: str,
    log_level: str = settings.app.log_level,
) -> None:
    debug = settings.app.debug
    handlers: list[logging.Handler] = []

    if debug:
        handlers.append(logging.StreamHandler())
    else:
        log_dir = settings.app.log_dir
        log_dir.mkdir(parents=True, exist_ok=True)
        handlers.append(
            RotatingFileHandler(
                filename=log_dir / f'{service_name}.log',
                maxBytes=50 * 1024 * 1024,
                backupCount=10,
                encoding='utf-8',
            )
        )

    if debug:
        logging.basicConfig(level=log_level, handlers=handlers)
    else:
        logging.basicConfig(
            format='%(message)s',
            level=log_level,
            handlers=handlers,
        )

    processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.filter_by_level,
        structlog.processors.TimeStamper(fmt='iso'),
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]
    if debug:
        processors.append(structlog.dev.ConsoleRenderer())
    else:
        processors.append(
            structlog.processors.JSONRenderer(
                sort_keys=True,
                ensure_ascii=False,
            ),
        )

    structlog.configure(
        context_class=dict,
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=False,
    )
