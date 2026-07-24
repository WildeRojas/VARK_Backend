"""
Tareas Celery para el motor de recomendación:
  - CU-16: Actualizar perfil VARK dinámicamente con decaimiento temporal
"""

import logging
import math
from datetime import timedelta

from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)

VARK_KEYS = ['V', 'A', 'R', 'K']

# Peso base por tipo de evento (antes de aplicar decaimiento temporal)
PESO_EVENTO = {
    'clic': 1.0,
    'permanencia': 2.0,   # mayor peso que un simple clic
    'retorno': 1.5,
    'cierre': 0.3,        # señal débil
}


@shared_task(name='recomendacion.actualizar_perfiles_vark')
def actualizar_perfiles_vark():
    """
    CU-16: Tarea periódica de Celery.
    Para cada estudiante con eventos Clickstream no procesados:
      1. Calcula un delta VARK ponderado con decaimiento temporal
      2. Combina el delta con el perfil existente (interpolación)
      3. Guarda el nuevo vector normalizado en PerfilVARK
      4. Registra el cambio en HistorialPerfilVARK
      5. Marca los eventos como procesados
    """
    from apps.accounts.models import PerfilVARK
    from apps.recomendacion.models import (
        ConfiguracionMotor,
        EventoClickstream,
        HistorialPerfilVARK,
    )

    config = ConfiguracionMotor.obtener()
    ahora = timezone.now()
    ventana = ahora - timedelta(days=config.dias_ventana_clickstream)

    estudiantes_ids = (
        EventoClickstream.objects.filter(procesado=False, timestamp__gte=ventana)
        .values_list('estudiante_id', flat=True)
        .distinct()
    )

    procesados_total = 0

    for estudiante_id in estudiantes_ids:
        try:
            _actualizar_perfil_estudiante(
                estudiante_id, config, ahora, ventana
            )
            procesados_total += 1
        except Exception as exc:
            logger.error(
                'Error actualizando perfil estudiante %s: %s', estudiante_id, exc
            )

    logger.info('Perfiles VARK actualizados: %d estudiantes', procesados_total)
    return {'estudiantes_actualizados': procesados_total}


def _actualizar_perfil_estudiante(estudiante_id, config, ahora, ventana):
    from apps.accounts.models import PerfilVARK
    from apps.recomendacion.models import (
        EventoClickstream,
        HistorialPerfilVARK,
    )

    eventos = list(
        EventoClickstream.objects.filter(
            estudiante_id=estudiante_id,
            procesado=False,
            timestamp__gte=ventana,
        ).select_related('recurso')
    )

    if not eventos:
        return

    # ── 1. Calcular vector delta con decaimiento temporal ──────────────────
    delta = {k: 0.0 for k in VARK_KEYS}
    total_peso = 0.0

    for evento in eventos:
        categoria = evento.recurso.categoria_vark
        if categoria not in VARK_KEYS:
            continue

        dias_antiguedad = max(0, (ahora - evento.timestamp).total_seconds() / 86400)
        decaimiento = math.pow(config.factor_decaimiento, dias_antiguedad)
        peso_base = PESO_EVENTO.get(evento.tipo_evento, 1.0)

        # Para permanencia, escalar por duración (máx 30 min = 1800 seg)
        if evento.tipo_evento == 'permanencia' and evento.duracion_segundos:
            factor_duracion = min(evento.duracion_segundos / 1800, 1.0)
            peso_base *= (1 + factor_duracion)

        peso_final = peso_base * decaimiento
        delta[categoria] += peso_final
        total_peso += peso_final

    if total_peso == 0:
        return

    # Normalizar delta
    delta_normalizado = {k: v / total_peso for k, v in delta.items()}

    # ── 2. Obtener perfil actual del estudiante ────────────────────────────
    try:
        perfil = PerfilVARK.objects.get(usuario_id=estudiante_id)
    except PerfilVARK.DoesNotExist:
        logger.warning('PerfilVARK no existe para estudiante %s', estudiante_id)
        return

    if not perfil.test_completado:
        return

    vector_anterior = {
        'V': perfil.puntaje_visual,
        'A': perfil.puntaje_auditivo,
        'R': perfil.puntaje_lectura,
        'K': perfil.puntaje_kinestesico,
    }

    # ── 3. Interpolar: 70% perfil actual + 30% señal nueva ────────────────
    ALPHA = 0.70
    BETA = 0.30

    vector_nuevo_raw = {
        k: ALPHA * vector_anterior[k] + BETA * delta_normalizado[k]
        for k in VARK_KEYS
    }

    # Re-normalizar para garantizar suma = 1.0
    suma = sum(vector_nuevo_raw.values())
    vector_nuevo = {k: v / suma for k, v in vector_nuevo_raw.items()}

    # ── 4. Guardar perfil actualizado ─────────────────────────────────────
    perfil.puntaje_visual = vector_nuevo['V']
    perfil.puntaje_auditivo = vector_nuevo['A']
    perfil.puntaje_lectura = vector_nuevo['R']
    perfil.puntaje_kinestesico = vector_nuevo['K']
    perfil.save(update_fields=[
        'puntaje_visual', 'puntaje_auditivo', 'puntaje_lectura', 'puntaje_kinestesico'
    ])

    # ── 5. Registrar en historial ─────────────────────────────────────────
    HistorialPerfilVARK.objects.create(
        estudiante_id=estudiante_id,
        vector_anterior=vector_anterior,
        vector_nuevo=vector_nuevo,
        origen=HistorialPerfilVARK.ORIGEN_CLICKSTREAM,
    )

    # ── 6. Marcar eventos como procesados ─────────────────────────────────
    EventoClickstream.objects.filter(
        pk__in=[e.pk for e in eventos]
    ).update(procesado=True)
