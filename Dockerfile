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

# Instalar dependencias Python (gunicorn y whitenoise se agregan explícitamente
# porque requirements.txt está en UTF-16 y el append de estas librerías falló)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn==23.0.0 whitenoise==6.9.0

# Copiar código fuente
COPY . .

# Variables de entorno requeridas en build
ENV DJANGO_SETTINGS_MODULE=config.settings.production

# collectstatic necesita cargar los settings, que a su vez requieren vars de entorno.
# Se pasan valores placeholder solo para este paso del build (no se usan en runtime).
RUN SECRET_KEY=placeholder-build-only \
    ALLOWED_HOSTS=localhost \
    DB_NAME=x \
    DB_USER=x \
    DB_PASSWORD=x \
    DB_HOST=x \
    GROQ_API_KEY=x \
    python manage.py collectstatic --noinput

# Cloud Run inyecta la variable PORT (default 8080)
ENV PORT=8080
EXPOSE 8080

# Aplicar migraciones pendientes y arrancar gunicorn
CMD python manage.py migrate --noinput && \
    gunicorn --bind 0.0.0.0:$PORT \
             --workers 2 \
             --timeout 120 \
             --access-logfile - \
             config.wsgi:application
