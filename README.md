# Payments service

Асинхронный сервис процессинга платежей на FastAPI, SQLAlchemy 2.0,
PostgreSQL, RabbitMQ и FastStream.

## Возможности

- создание платежа с защитой от дублей по `Idempotency-Key`;
- получение текущего состояния платежа;
- атомарная запись платежа и события посредством Outbox pattern;
- асинхронная обработка из очереди `payments.new`;
- эмуляция платёжного шлюза: 2–5 секунд, 90% успешных платежей;
- webhook с результатом обработки;
- три попытки обработки с задержками 2 и 4 секунды;
- Dead Letter Queue `payments.new.dlq` после третьей ошибки.

## Запуск

Требуются Docker и Docker Compose.

```bash
docker compose up -d --build
```

Compose запускает PostgreSQL, RabbitMQ, миграции Alembic, API, consumer и
Outbox relay. Миграции применяются автоматически.

- Swagger UI: <http://localhost:8000/docs>
- RabbitMQ UI: <http://localhost:15672>
- RabbitMQ login/password: `payments` / `payments`
- API key для локального окружения: `development-secret`

Остановить сервисы:

```bash
docker compose down
```

## API

Все эндпоинты требуют заголовок:

```text
X-API-Key: development-secret
```

### Создание платежа

`POST /api/v1/payments`

```bash
curl -i -X POST http://localhost:8000/api/v1/payments \
  -H 'X-API-Key: development-secret' \
  -H "Idempotency-Key: $(uuidgen)" \
  -H 'Content-Type: application/json' \
  -d '{
    "amount": "1250.50",
    "currency": "RUB",
    "description": "Test payment",
    "webhook_url": "https://example.com/payment-webhook",
    "meta_data": {"order_id": "order-42"}
  }'
```

Ответ `202 Accepted`:

```json
{
  "payment_id": "0199c8d4-2dc0-7000-8000-000000000001",
  "status": "pending",
  "created_at": "2026-10-14T10:00:00Z"
}
```

Повторный запрос с тем же `Idempotency-Key` возвращает существующий платёж и
не создаёт повторное событие.

### Получение платежа

`GET /api/v1/payments/{payment_id}`

```bash
curl http://localhost:8000/api/v1/payments/<payment-id> \
  -H 'X-API-Key: development-secret'
```

Ответ содержит сумму, валюту, описание, метаданные, webhook URL, статус и даты
создания и обработки. Возможные статусы: `pending`, `succeeded`, `failed`.

## Обработка сообщений

API сохраняет платёж и Outbox-событие в одной транзакции. Outbox relay
публикует событие в `payments.new`, после чего consumer обрабатывает платёж,
обновляет его статус и отправляет webhook.

При технической ошибке сообщение повторяется через 2 и 4 секунды. После
третьей неудачной обработки RabbitMQ перемещает его в `payments.new.dlq`.

## Тесты

Unit- и транспортные тесты не требуют внешних сервисов:

```bash
uv sync --group test
set -a
source .env.example
set +a
uv run pytest -m 'unit or e2e'
```

Для полного набора с PostgreSQL-интеграциями:

```bash
docker compose up -d postgres
cp .env.example .env
set -a
source .env
set +a
DB_NAME=payments_test uv run alembic upgrade head
uv run pytest
```
