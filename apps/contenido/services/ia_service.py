import json
import logging

from django.conf import settings

logger = logging.getLogger(__name__)

PROMPT_SUGERIR_RECURSOS = """Eres un experto en recursos educativos para programación.

Sugiere exactamente {cantidad} recursos educativos en línea para estudiantes universitarios de programación básica.

Parámetros:
- Tema: {tema}
- Estilo de aprendizaje VARK: {estilo_nombre} ({estilo_codigo})
- Nivel de complejidad sugerido: {nivel}

Criterios para el estilo {estilo_codigo}:
{criterios_estilo}

Reglas:
- Todos los recursos deben ser accesibles de forma gratuita.
- URLs deben ser reales y verificables.
- El campo "justificacion_pedagogica" debe explicar por qué el recurso encaja con el estilo VARK indicado.
- Todo en español.

Responde ÚNICAMENTE con JSON válido, sin bloques markdown, con esta estructura:
{{
  "recursos": [
    {{
      "titulo": "Nombre del recurso",
      "url": "https://...",
      "descripcion": "Descripción breve del recurso",
      "tipo_formato": "video|articulo|ejercicio|documento",
      "justificacion_pedagogica": "Por qué encaja con el estilo {estilo_codigo}"
    }}
  ]
}}"""

CRITERIOS_VARK = {
    'V': 'Recursos visuales: videos explicativos, infografías, diagramas animados, presentaciones visuales.',
    'A': 'Recursos auditivos: podcasts, videos con narración, explicaciones orales, clases grabadas.',
    'R': 'Recursos de lectura/escritura: artículos técnicos, documentación oficial, tutoriales escritos, libros.',
    'K': 'Recursos kinestésicos: ejercicios interactivos, desafíos de código (coding challenges), proyectos prácticos, sandboxes.',
}

NOMBRES_VARK = {
    'V': 'Visual',
    'A': 'Auditivo',
    'R': 'Lectura/Escritura',
    'K': 'Kinestésico',
}


def sugerir_recursos_ia(tema_nombre, categoria_vark, nivel='basico', cantidad=8):
    """
    Llama a Groq para obtener sugerencias de recursos educativos.

    Args:
        tema_nombre: str — nombre del tema (ej: "Vectores")
        categoria_vark: str — 'V', 'A', 'R' o 'K'
        nivel: str — 'basico', 'intermedio', 'avanzado'
        cantidad: int — número de recursos solicitados (entre 5 y 10)

    Returns:
        list[dict] — lista de recursos con: titulo, url, descripcion,
                     tipo_formato, justificacion_pedagogica
    """
    cantidad = max(5, min(10, cantidad))

    prompt = PROMPT_SUGERIR_RECURSOS.format(
        tema=tema_nombre,
        estilo_codigo=categoria_vark,
        estilo_nombre=NOMBRES_VARK.get(categoria_vark, categoria_vark),
        nivel=nivel,
        cantidad=cantidad,
        criterios_estilo=CRITERIOS_VARK.get(categoria_vark, ''),
    )

    try:
        from groq import Groq
        client = Groq(api_key=settings.GROQ_API_KEY)

        response = client.chat.completions.create(
            model=settings.GROQ_MODEL,
            messages=[{'role': 'user', 'content': prompt}],
            temperature=0.6,
            max_tokens=3000,
        )

        content = response.choices[0].message.content.strip()

        if '```json' in content:
            content = content.split('```json')[1].split('```')[0].strip()
        elif '```' in content:
            content = content.split('```')[1].split('```')[0].strip()

        data = json.loads(content)
        recursos = data.get('recursos', [])

        if not recursos:
            raise ValueError('Groq retornó una lista vacía de recursos.')

        tipos_validos = {'video', 'articulo', 'ejercicio', 'documento'}
        for r in recursos:
            if r.get('tipo_formato') not in tipos_validos:
                r['tipo_formato'] = 'articulo'

        return recursos

    except Exception as exc:
        logger.error('Error al sugerir recursos via Groq: %s', exc)
        raise


# ─── Fase 4: Generación de preguntas de quiz con IA ───────────────────────────

PROMPT_PREGUNTAS_QUIZ = """Eres un experto en didáctica de la programación.

Genera exactamente {cantidad} preguntas de opción múltiple en español para evaluar a estudiantes universitarios sobre el tema "{tema}".

Parámetros:
- Tema: {tema}
- Nivel de dificultad: {dificultad}

Reglas:
- Cada pregunta debe tener exactamente 4 opciones.
- Exactamente UNA opción correcta; las otras 3 deben ser distractores plausibles.
- Incluye una breve "explicacion" (retroalimentación) que justifique la respuesta correcta.
- Las preguntas deben ser claras, sin ambigüedad, y acordes a la dificultad indicada.
- Todo en español.

Responde ÚNICAMENTE con JSON válido, sin bloques markdown, con esta estructura exacta:
{{
  "preguntas": [
    {{
      "enunciado": "texto de la pregunta",
      "explicacion": "por qué la respuesta correcta es correcta",
      "opciones": [
        {{"texto": "opción 1", "es_correcta": true}},
        {{"texto": "opción 2", "es_correcta": false}},
        {{"texto": "opción 3", "es_correcta": false}},
        {{"texto": "opción 4", "es_correcta": false}}
      ]
    }}
  ]
}}"""

DIFICULTAD_NOMBRE = {'facil': 'Fácil', 'media': 'Media', 'dificil': 'Difícil'}


def generar_preguntas_quiz(tema_nombre, dificultad='facil', cantidad=5):
    """
    Llama a Groq para generar preguntas de quiz candidatas (no las guarda).

    Returns:
        list[dict] — cada una: {enunciado, explicacion, opciones:[{texto, es_correcta}]}

    Lanza una excepción si la IA falla o devuelve un formato inválido
    (el frontend mantiene la creación manual como respaldo).
    """
    cantidad = max(1, min(10, cantidad))
    prompt = PROMPT_PREGUNTAS_QUIZ.format(
        tema=tema_nombre,
        dificultad=DIFICULTAD_NOMBRE.get(dificultad, dificultad),
        cantidad=cantidad,
    )

    from groq import Groq
    client = Groq(api_key=settings.GROQ_API_KEY)

    response = client.chat.completions.create(
        model=settings.GROQ_MODEL,
        messages=[{'role': 'user', 'content': prompt}],
        temperature=0.6,
        max_tokens=3500,
    )

    content = response.choices[0].message.content.strip()
    if '```json' in content:
        content = content.split('```json')[1].split('```')[0].strip()
    elif '```' in content:
        content = content.split('```')[1].split('```')[0].strip()

    data = json.loads(content)
    preguntas = data.get('preguntas', [])
    if not preguntas:
        raise ValueError('La IA no devolvió preguntas.')

    # Validar/normalizar: 4 opciones y exactamente 1 correcta
    validadas = []
    for p in preguntas:
        opciones = p.get('opciones', [])
        if len(opciones) < 2:
            continue
        correctas = [o for o in opciones if o.get('es_correcta')]
        if len(correctas) != 1:
            # Forzar la primera como correcta si la IA no marcó exactamente una
            for i, o in enumerate(opciones):
                o['es_correcta'] = (i == 0)
        validadas.append({
            'enunciado': p.get('enunciado', '').strip(),
            'explicacion': p.get('explicacion', '').strip(),
            'opciones': [
                {'texto': str(o.get('texto', '')).strip(), 'es_correcta': bool(o.get('es_correcta'))}
                for o in opciones
            ],
        })

    if not validadas:
        raise ValueError('La IA no devolvió preguntas válidas.')

    return validadas
