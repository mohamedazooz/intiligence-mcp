FROM python:3.13-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    INTILIGENCE_SOURCE_REGISTRY_PATH=/app/.data/sources.sqlite3

WORKDIR /app
RUN groupadd --gid 10001 app && useradd --uid 10001 --gid app --create-home --shell /usr/sbin/nologin app
COPY pyproject.toml README.md ./
COPY src ./src
RUN python -m pip install --no-cache-dir ".[distributed]"
RUN mkdir -p /app/.data && chown -R app:app /app

USER 10001:10001
ENTRYPOINT ["intiligence-mcp"]
