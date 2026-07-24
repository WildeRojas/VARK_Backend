# ─── Etapa única: producción ──────────────────────────────────────────────────
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Dependencias de sistema para psycopg2
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Instalar dependencias Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código fuente
COPY . .

# Variables de entorno requeridas en build
ENV DJANGO_SETTINGS_MODULE=config.settings.production

# collectstatic necesita cargar los settings
RUN SECRET_KEY=placeholder-build-only \
    ALLOWED_HOSTS=localhost \
    DB_NAME=x \
    DB_USER=x \
    DB_PASSWORD=x \
    DB_HOST=x \
    GROQ_API_KEY=x \
    python manage.py collectstatic --noinput

# Aplicar migraciones pendientes y arrancar gunicorn en el puerto dinámico de Railway ($PORT)
CMD ["sh", "-c", "python manage.py migrate --noinput && gunicorn --bind 0.0.0.0:${PORT:-8000} --workers 2 --timeout 120 --access-logfile - config.wsgi:application"]
