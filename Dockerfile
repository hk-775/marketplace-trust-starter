FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    MTS_HOST=0.0.0.0 \
    MTS_PORT=8101 \
    MTS_DATABASE_PATH=/data/marketplace_trust_starter.db

WORKDIR /app

COPY pyproject.toml README.md LICENSE NOTICE ./
COPY src/ src/

RUN python -m pip install --no-cache-dir . \
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

