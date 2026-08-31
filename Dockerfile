FROM ghcr.io/astral-sh/uv:0.10.7 AS uv

FROM python:3.12.11-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    MTS_HOST=0.0.0.0 \
    MTS_PORT=8101 \
    MTS_DATABASE_PATH=/data/marketplace_trust_starter.db \
    PATH=/app/.venv/bin:$PATH

WORKDIR /app

COPY --from=uv /uv /uvx /bin/
COPY pyproject.toml uv.lock README.md LICENSE NOTICE ./
COPY src/ src/

RUN uv sync --locked --no-dev --no-editable \
    && addgroup --system --gid 10001 truststarter \
    && adduser --system --uid 10001 --ingroup truststarter \
        --home /nonexistent --no-create-home truststarter \
    && mkdir -p /data \
    && chown 10001:10001 /data \
    && chown -R root:root /app \
    && chmod -R a-w /app

VOLUME ["/data"]
EXPOSE 8101
USER 10001:10001

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8101/api/v1/health', timeout=3)"]

CMD ["marketplace-trust-starter", "--host", "0.0.0.0", "--port", "8101"]
