# Production image (specs/014): gunicorn + whitenoise, deps via uv.
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy

# Install dependencies before copying the source so the layer caches.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project --no-dev

COPY . .
RUN uv sync --frozen --no-dev

# collectstatic imports settings, so the required env vars need dummy
# values at build time; no database is touched.
RUN SECRET_KEY=build-only \
    POSTGRES_DB=x POSTGRES_USER=x POSTGRES_PASSWORD=x \
    POSTGRES_HOST=x POSTGRES_PORT=5432 \
    uv run --no-sync python manage.py collectstatic --noinput

EXPOSE 8000

# Migrations run on every start (idempotent); this is how deploys apply
# schema changes (specs/014).
CMD ["sh", "-c", "uv run --no-sync python manage.py migrate --noinput && uv run --no-sync gunicorn cream.wsgi:application --bind 0.0.0.0:8000 --workers 3"]
