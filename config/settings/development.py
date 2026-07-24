"""
Settings de desarrollo — extiende base.py
"""

from .base import *

DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1']

# Base de datos PostgreSQL (desarrollo)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST', default='localhost'),
        'PORT': config('DB_PORT', default='5432'),
    }
}

# En desarrollo mostramos el SQL generado en consola
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {'class': 'logging.StreamHandler'},
    },
    'loggers': {
        # 'django.db.backends': {
        #     'handlers': ['console'],
        #     'level': 'DEBUG',
        # },
        
        # podemos activar el logging de Django para ver las consultas SQL en desarrollo, pero de momento lo dejamos comentado para no saturar la consola. Si quieres activarlo, simplemente descomenta el bloque correspondiente.
    },
}
