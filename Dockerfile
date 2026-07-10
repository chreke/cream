# Production image (specs/014): gunicorn + whitenoise.
#
# Dependencies come from requirements.txt, which is *generated* from
# uv.lock — regenerate it after changing dependencies:
#
#     uv export --no-dev --no-emit-project -o requirements.txt
FROM python:3.13-slim

ENV PYTHONUNBUFFERED=1
WORKDIR /app

# Install dependencies before copying the source so the layer caches.
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# collectstatic imports settings, so the required env vars need dummy
# values at build time; no database is touched.
RUN SECRET_KEY=build-only \
    POSTGRES_DB=x POSTGRES_USER=x POSTGRES_PASSWORD=x \
    POSTGRES_HOST=x POSTGRES_PORT=5432 \
    python manage.py collectstatic --noinput

EXPOSE 8000

# Migrations run on every start (idempotent); this is how deploys apply
# schema changes (specs/014).
CMD ["sh", "-c", "python manage.py migrate --noinput && gunicorn cream.wsgi:application --bind 0.0.0.0:8000 --workers 3"]
