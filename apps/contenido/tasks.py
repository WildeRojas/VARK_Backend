import logging
from datetime import timedelta

import httpx
from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)

TIMEOUT_SEGUNDOS = 10


@shared_task(name='contenido.validar_urls_recursos')
def validar_urls_recursos():
    """
    Tarea periódica de Celery: verifica que las URLs de todos los recursos
    activos sigan respondiendo. Marca url_valida=False si la URL no responde.
    """
    from .models import Recurso

    recursos = Recurso.objects.filter(activo=True)
    actualizados = 0

    for recurso in recursos:
        valida = _verificar_url(recurso.url)
        if recurso.url_valida != valida:
            recurso.url_valida = valida
            recurso.ultima_verificacion = timezone.now()
            recurso.save(update_fields=['url_valida', 'ultima_verificacion'])
            actualizados += 1
        else:
            recurso.ultima_verificacion = timezone.now()
            recurso.save(update_fields=['ultima_verificacion'])

    logger.info('Validación de URLs completada. Recursos actualizados: %d', actualizados)
    return {'verificados': recursos.count(), 'actualizados': actualizados}


def _verificar_url(url):
    """
    Realiza un HEAD (con fallback a GET) a la URL.
    Retorna True si responde con código HTTP < 400.
    """
    try:
        with httpx.Client(timeout=TIMEOUT_SEGUNDOS, follow_redirects=True) as client:
            response = client.head(url)
            if response.status_code < 400:
                return True
            # Algunos servidores no aceptan HEAD, intentar GET
            response = client.get(url)
            return response.status_code < 400
    except Exception as exc:
        logger.debug('URL no accesible %s: %s', url, exc)
        return False
