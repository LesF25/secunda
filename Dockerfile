FROM python:3.14-slim-bookworm AS builder

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    UV_VERSION=0.10.10

COPY pyproject.toml uv.lock ./
RUN pip install --no-cache-dir "uv==$UV_VERSION" \
    && uv sync --frozen --no-dev --no-install-project

FROM python:3.14-slim-bookworm AS runtime

WORKDIR /app

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN groupadd --system app \
    && useradd --system --gid app --home-dir /app app \
    && mkdir -p /app/logs \
    && chown app:app /app/logs

COPY --from=builder --chown=app:app /app/.venv /app/.venv
COPY --chown=app:app alembic.ini ./
COPY --chown=app:app migrations ./migrations
COPY --chown=app:app src ./src

USER app

CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
