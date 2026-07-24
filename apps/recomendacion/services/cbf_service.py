"""
Motor de Content-Based Filtering (CBF) para CU-12 y CU-13.

Algoritmo:
  1. Obtener el vector VARK actual del estudiante: {V, A, R, K} (suma = 1.0)
  2. Construir el vector de cada recurso del tema activo:
       recurso_vec = {categoria_vark: 1.0, resto: 0.0}
  3. Calcular similitud coseno entre vector_estudiante y vector_recurso
  4. Penalizar recursos ya valorados como "no_util" por el estudiante
  5. Bonificar recursos ya valorados como "util"
  6. Ordenar por puntuación final y retornar los top-N
  7. Generar justificación en lenguaje natural con Groq (CU-13)
"""

import logging
import math

logger = logging.getLogger(__name__)

VARK_KEYS = ['V', 'A', 'R', 'K']

PLANTILLAS_JUSTIFICACION = {
    'V': (
        'Te recomendamos este recurso porque tu perfil muestra mayor afinidad con el '
        'aprendizaje visual (puntuación V={puntaje_v:.0%}). Este recurso de tipo '
        '"{tipo_formato}" te permitirá comprender el tema de {tema} a través de '
        'representaciones gráficas y visuales.'
    ),
    'A': (
        'Tu perfil indica preferencia por el aprendizaje auditivo (A={puntaje_a:.0%}). '
        'Este recurso "{tipo_formato}" sobre {tema} está diseñado para quienes aprenden '
        'mejor escuchando explicaciones y narrativas orales.'
    ),
    'R': (
        'Dado tu perfil de lectura/escritura (R={puntaje_r:.0%}), te recomendamos este '
        '"{tipo_formato}" que te permitirá explorar {tema} con documentación detallada '
        'y texto estructurado.'
    ),
    'K': (
        'Tu perfil kinestésico (K={puntaje_k:.0%}) indica que aprendes mejor con la '
        'práctica. Este recurso de tipo "{tipo_formato}" sobre {tema} incluye ejercicios '
        'y actividades prácticas ideales para tu estilo.'
    ),
}


def _similitud_coseno(vec_estudiante: dict, categoria_vark: str) -> float:
    """
    Similitud coseno entre el vector VARK del estudiante y el vector del recurso.
    El vector del recurso tiene 1.0 en su categoría y 0 en el resto.
    """
    dot = vec_estudiante.get(categoria_vark, 0.0)
    mag_estudiante = math.sqrt(sum(v ** 2 for v in vec_estudiante.values()))
    if mag_estudiante == 0:
        return 0.0
    # mag_recurso = 1.0 (vector unitario), así que similitud = dot / mag_estudiante
    return dot / mag_estudiante


def recomendar_recursos(estudiante, tema_id, config=None):
    """
    Genera recomendaciones CBF para un estudiante en un tema dado.

    Args:
        estudiante: instancia de Usuario con perfil VARK completado
        tema_id: int
        config: instancia de ConfiguracionMotor (se obtiene automáticamente si es None)

    Returns:
        list[dict] con: recurso, puntuacion, justificacion
    """
    from apps.contenido.models import Recurso, Tema
    from apps.recomendacion.models import ConfiguracionMotor, ValoracionRecurso

    if config is None:
        config = ConfiguracionMotor.obtener()

    try:
        perfil = estudiante.perfil_vark
    except Exception:
        return []

    if not perfil.test_completado:
        return []

    vector = perfil.vector  # {V, A, R, K} sumando 1.0

    try:
        tema = Tema.objects.get(pk=tema_id, activo=True)
    except Tema.DoesNotExist:
        return []

    recursos = list(
        Recurso.objects.filter(tema=tema, activo=True, url_valida=True)
        .select_related('tema', 'subtema')
    )

    if not recursos:
        return []

    # Obtener valoraciones previas del estudiante para ajustar puntuación
    valoraciones = {
        v.recurso_id: v.valoracion
        for v in ValoracionRecurso.objects.filter(estudiante=estudiante)
    }

    # ── Fase 5: ¿hay modelo ML entrenado y activo? ────────────────────────────
    clics_map, perm_map, usar_ml = _preparar_ml(estudiante, recursos, config)

    resultados = []
    for recurso in recursos:
        # CBF heurístico (similitud coseno + ajuste por valoración)
        cbf = _similitud_coseno(vector, recurso.categoria_vark)
        val = valoraciones.get(recurso.pk)
        if val == 'util':
            cbf = min(1.0, cbf + config.peso_valoracion_util)
        elif val == 'no_util':
            cbf *= 0.3  # Penalizar fuertemente

        # Mezcla con la probabilidad de utilidad del modelo ML (si está disponible)
        puntuacion = cbf
        if usar_ml:
            from apps.recomendacion.services.ml import inference as ml_inf
            prob = ml_inf.predecir_utilidad(
                vector, recurso.categoria_vark, recurso.nivel_complejidad,
                recurso.tipo_formato, clics_map.get(recurso.pk, 0), perm_map.get(recurso.pk, 0),
            )
            if prob is not None:
                puntuacion = config.peso_cbf * cbf + config.peso_ml * prob

        if puntuacion >= config.umbral_similitud:
            justificacion = _generar_justificacion_local(recurso, vector, tema.nombre)
            resultados.append({
                'recurso': recurso,
                'puntuacion': round(puntuacion, 4),
                'justificacion': justificacion,
            })

    resultados.sort(key=lambda x: x['puntuacion'], reverse=True)
    return resultados[: config.max_recomendaciones]


def _preparar_ml(estudiante, recursos, config):
    """
    Prepara los insumos para el modelo ML: agregados de clickstream del estudiante
    sobre los recursos candidatos y la bandera de si se debe usar ML.

    Returns: (clics_map, perm_map, usar_ml)
    """
    from collections import defaultdict

    if not getattr(config, 'usar_ml', False):
        return {}, {}, False

    try:
        from apps.recomendacion.services.ml import inference as ml_inf
        if not ml_inf.modelo_disponible():
            return {}, {}, False
    except Exception:
        return {}, {}, False

    from apps.recomendacion.models import EventoClickstream

    clics_map = defaultdict(int)
    perm_map = defaultdict(int)
    rec_ids = [r.pk for r in recursos]
    for ev in EventoClickstream.objects.filter(
        estudiante=estudiante, recurso_id__in=rec_ids
    ).values('recurso_id', 'tipo_evento', 'duracion_segundos'):
        if ev['tipo_evento'] == 'clic':
            clics_map[ev['recurso_id']] += 1
        elif ev['tipo_evento'] == 'permanencia':
            perm_map[ev['recurso_id']] += (ev['duracion_segundos'] or 0)

    return clics_map, perm_map, True


# ─── Fase 6: Experimento A/B — el grupo cambia la experiencia ─────────────────

def grupo_experimento_activo(estudiante):
    """
    Devuelve el grupo ('experimental' | 'control') del estudiante en el
    experimento A/B **activo** más reciente, o None si no está en ninguno.
    """
    try:
        from apps.analitica.models import AsignacionExperimento, ExperimentoAB
    except Exception:
        return None
    asignacion = (
        AsignacionExperimento.objects
        .filter(estudiante=estudiante, experimento__estado=ExperimentoAB.ESTADO_ACTIVO)
        .order_by('-fecha_asignacion')
        .first()
    )
    return asignacion.grupo if asignacion else None


def recomendar_sin_personalizacion(tema_id, config=None):
    """
    Recomendación para el grupo de CONTROL: recursos del tema **sin** usar el
    vector VARK (orden por recencia). Sirve como línea base del experimento A/B.

    Returns:
        list[dict] con: recurso, puntuacion (0.0), justificacion
    """
    from apps.contenido.models import Recurso, Tema
    from apps.recomendacion.models import ConfiguracionMotor

    if config is None:
        config = ConfiguracionMotor.obtener()

    try:
        tema = Tema.objects.get(pk=tema_id, activo=True)
    except Tema.DoesNotExist:
        return []

    recursos = list(
        Recurso.objects.filter(tema=tema, activo=True, url_valida=True)
        .select_related('tema', 'subtema')
        .order_by('-fecha_creacion')[: config.max_recomendaciones]
    )

    justificacion = (
        'Recurso de {tema} mostrado sin personalización por estilo de aprendizaje '
        '(grupo de control del experimento A/B).'
    )
    return [
        {
            'recurso': r,
            'puntuacion': 0.0,
            'justificacion': justificacion.format(tema=tema.nombre),
        }
        for r in recursos
    ]


def _generar_justificacion_local(recurso, vector, tema_nombre):
    """Genera justificación usando plantillas locales (sin llamada a API)."""
    plantilla = PLANTILLAS_JUSTIFICACION.get(recurso.categoria_vark, '')
    return plantilla.format(
        puntaje_v=vector.get('V', 0),
        puntaje_a=vector.get('A', 0),
        puntaje_r=vector.get('R', 0),
        puntaje_k=vector.get('K', 0),
        tipo_formato=recurso.get_tipo_formato_display(),
        tema=tema_nombre,
    )


def generar_justificacion_groq(recurso, vector, tema_nombre):
    """
    CU-13: genera justificación personalizada via Groq.
    Retorna el texto generado o None si falla (el caller usa la plantilla local).
    """
    from django.conf import settings

    prompt = (
        f'Un estudiante tiene el siguiente perfil de aprendizaje VARK: '
        f'Visual={vector.get("V", 0):.0%}, Auditivo={vector.get("A", 0):.0%}, '
        f'Lectura/Escritura={vector.get("R", 0):.0%}, Kinestésico={vector.get("K", 0):.0%}. '
        f'Se le recomienda el recurso "{recurso.titulo}" (tipo: {recurso.get_tipo_formato_display()}, '
        f'categoría VARK: {recurso.get_categoria_vark_display()}) sobre el tema "{tema_nombre}". '
        f'Escribe en 2 oraciones, en español, una justificación personalizada explicando '
        f'por qué este recurso encaja con su perfil de aprendizaje. '
        f'Sé concreto y menciona el estilo dominante del estudiante.'
    )

    try:
        from groq import Groq
        client = Groq(api_key=settings.GROQ_API_KEY)
        response = client.chat.completions.create(
            model=settings.GROQ_MODEL,
            messages=[{'role': 'user', 'content': prompt}],
            temperature=0.5,
            max_tokens=200,
        )
        return response.choices[0].message.content.strip()
    except Exception as exc:
        logger.warning('Groq justificación falló, usando plantilla local: %s', exc)
        return None
