import json
import logging
import urllib.request
import urllib.error

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
}}
"""

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


def _llamar_gemini_json(prompt):
    """Llama a Google Gemini REST API con soporte para gemini-2.5-flash y fallbacks."""
    api_key = getattr(settings, 'GEMINI_API_KEY', '').strip('"\'') 
    if not api_key:
        raise ValueError('GEMINI_API_KEY no está configurada.')

    configured_model = getattr(settings, 'GEMINI_MODEL', 'gemini-2.5-flash').strip('"\'')
    models_to_try = [configured_model, 'gemini-2.5-flash', 'gemini-2.5-pro', 'gemini-1.5-flash']
    # Remove duplicates preserving order
    models_to_try = list(dict.fromkeys(models_to_try))

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.4,
            "responseMimeType": "application/json",
        },
    }

    last_err = None
    for model in models_to_try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode('utf-8'),
            headers={'Content-Type': 'application/json'},
            method='POST',
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                res_data = json.loads(resp.read().decode('utf-8'))
                candidates = res_data.get('candidates', [])
                if candidates and 'content' in candidates[0]:
                    parts = candidates[0]['content'].get('parts', [])
                    if parts and 'text' in parts[0]:
                        return parts[0]['text'].strip()
        except Exception as exc:
            last_err = exc
            logger.warning('Fallo llamando a modelo Gemini %s: %s', model, exc)
            continue

    raise ValueError(f'Error al consultar Gemini API: {last_err}')


def _extraer_json(content):
    """Limpia wrappers de markdown si existen y parsea JSON."""
    content = content.strip()
    if '```json' in content:
        content = content.split('```json')[1].split('```')[0].strip()
    elif '```' in content:
        content = content.split('```')[1].split('```')[0].strip()
    return json.loads(content)


def sugerir_recursos_ia(tema_nombre, categoria_vark, nivel='basico', cantidad=8):
    """
    Llama a Groq (o Gemini como respaldo) para obtener sugerencias de recursos.
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

    content = None
    # 1. Intentar con Groq
    if getattr(settings, 'GROQ_API_KEY', ''):
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
        except Exception as exc:
            logger.warning('Groq no disponible para sugerir recursos (%s). Intentando con Gemini...', exc)

    # 2. Respaldo: Intentar con Gemini
    if not content and getattr(settings, 'GEMINI_API_KEY', ''):
        try:
            content = _llamar_gemini_json(prompt)
            logger.info('Sugerencias de recursos generadas exitosamente con Gemini de respaldo.')
        except Exception as exc:
            logger.error('Gemini tampoco pudo responder: %s', exc)

    if not content:
        raise ValueError('Ningún proveedor de IA (Groq ni Gemini) está disponible.')

    data = _extraer_json(content)
    recursos = data.get('recursos', [])

    if not recursos:
        raise ValueError('La IA retornó una lista vacía de recursos.')

    tipos_validos = {'video', 'articulo', 'ejercicio', 'documento'}
    for r in recursos:
        if r.get('tipo_formato') not in tipos_validos:
            r['tipo_formato'] = 'articulo'

    return recursos


# ─── Generación de preguntas de quiz con IA ───

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
}}
"""

DIFICULTAD_NOMBRE = {'facil': 'Fácil', 'media': 'Media', 'dificil': 'Difícil'}


def generar_preguntas_quiz(tema_nombre, dificultad='facil', cantidad=5):
    """
    Llama a Groq (o Gemini como respaldo) para generar preguntas de quiz candidatas.
    """
    cantidad = max(1, min(10, cantidad))
    prompt = PROMPT_PREGUNTAS_QUIZ.format(
        tema=tema_nombre,
        dificultad=DIFICULTAD_NOMBRE.get(dificultad, dificultad),
        cantidad=cantidad,
    )

    content = None
    # 1. Intentar con Groq
    if getattr(settings, 'GROQ_API_KEY', ''):
        try:
            from groq import Groq
            client = Groq(api_key=settings.GROQ_API_KEY)
            response = client.chat.completions.create(
                model=settings.GROQ_MODEL,
                messages=[{'role': 'user', 'content': prompt}],
                temperature=0.6,
                max_tokens=3500,
            )
            content = response.choices[0].message.content.strip()
        except Exception as exc:
            logger.warning('Groq no disponible para quiz (%s). Intentando con Gemini...', exc)

    # 2. Respaldo: Intentar con Gemini
    if not content and getattr(settings, 'GEMINI_API_KEY', ''):
        try:
            content = _llamar_gemini_json(prompt)
            logger.info('Preguntas de quiz generadas exitosamente con Gemini de respaldo.')
        except Exception as exc:
            logger.error('Gemini tampoco pudo generar quiz: %s', exc)

    if not content:
        raise ValueError('Ningún proveedor de IA (Groq ni Gemini) está disponible.')

    data = _extraer_json(content)
    preguntas = data.get('preguntas', [])
    if not preguntas:
        raise ValueError('La IA no devolvió preguntas.')

    validadas = []
    for p in preguntas:
        opciones = p.get('opciones', [])
        if len(opciones) < 2:
            continue
        correctas = [o for o in opciones if o.get('es_correcta')]
        if len(correctas) != 1:
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
