# syntax=docker/dockerfile:1.7
FROM python:3.13.13-slim-bookworm AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

COPY --from=ghcr.io/astral-sh/uv:0.11.33 /uv /uvx /bin/
WORKDIR /app

COPY pyproject.toml uv.lock ./

FROM base AS test
RUN uv sync --frozen --group dev
COPY app ./app
COPY tests ./tests
RUN uv run pytest -q \
    && uv run ruff check . \
    && uv run ruff format --check .

FROM base AS runtime
RUN uv sync --frozen --no-dev \
    && addgroup --system --gid 10001 app \
    && adduser --system --uid 10001 --gid 10001 --home /app app

RUN apt-get update \
    && apt-get install --yes --no-install-recommends --only-upgrade libgnutls30 \
    && rm -rf /var/lib/apt/lists/*

COPY --chown=10001:10001 app ./app

USER 10001:10001
EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=5 \
  CMD ["/app/.venv/bin/python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/health', timeout=2)"]

CMD ["/app/.venv/bin/uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--no-access-log"]
