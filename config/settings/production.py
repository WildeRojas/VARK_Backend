"""
Settings de producción — extiende base.py
"""

from .base import *

DEBUG = False

ALLOWED_HOSTS = config(
    'ALLOWED_HOSTS',
    default='*',
    cast=lambda v: [s.strip().strip('"\'') for s in v.split(',') if s.strip()],
)

# Base de datos PostgreSQL (producción)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME').strip('"\''),
        'USER': config('DB_USER').strip('"\''),
        'PASSWORD': config('DB_PASSWORD').strip('"\''),
        'HOST': config('DB_HOST').strip('"\''),
        'PORT': config('DB_PORT', default='5432').strip('"\''),
        'OPTIONS': {
            'sslmode': config('DB_SSLMODE', default='require').strip('"\''),
        },
    }
}

# Cloud Run / Railway termina SSL en el balanceador
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Seguridad
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

STATIC_ROOT = BASE_DIR / 'staticfiles'
STATIC_URL = '/static/'

# Whitenoise — sirve estáticos del admin directamente desde Gunicorn
MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')
STORAGES = {
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedStaticFilesStorage",
    },
}

