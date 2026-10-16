import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

import aiohttp
import structlog

from src.core.http_client import HttpClient
from src.core.http_client.parse_helpers import UnknownError, response_to_json
from src.payments.domain.entities.currency import Currency
from src.payments.domain.entities.payment_status import PaymentStatus

logger = structlog.getLogger(__name__)


class NotificationUnknownError(Exception):
    pass


async def notification_response_handler(response: aiohttp.ClientResponse) -> Any:
    status_code = response.status

    if response.ok:
        try:
            return await response_to_json(response)
        except UnknownError as exc:
            logger.warning('Response parsing failed', error=str(exc))
            return None

    response_text = await response.text()
    logger.error(
        'Webhook service unknown error',
        status_code=status_code,
        response=response_text[:1000],
    )
    raise NotificationUnknownError(
        f'Unexpected error: {status_code}, {response_text[:1000]}'
    )


class WebhookNotificationClient:
    def __init__(self, session: aiohttp.ClientSession) -> None:
        self._http_client = HttpClient(
            session=session,
            response_handler=notification_response_handler,
        )

    async def notify_webhook(
        self,
        webhook_url: str,
        payment_id: uuid.UUID,
        status: PaymentStatus,
        amount: Decimal,
        currency: Currency,
        processed_at: datetime | None,
    ) -> None:
        payload = {
            'payment_id': str(payment_id),
            'status': status.value,
            'amount': str(amount),
            'currency': currency.value,
            'processed_at': (
                processed_at.isoformat() if processed_at else None
            ),
        }
        headers = {
            'Idempotency-Key': f'payment-status:{payment_id}',
        }
        await self._http_client.request(
            method='POST',
            url=webhook_url,
            json=payload,
            headers=headers,
        )
