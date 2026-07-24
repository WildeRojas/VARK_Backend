import json
import logging

from django.conf import settings

logger = logging.getLogger(__name__)

# ─── Test estático de respaldo ────────────────────────────────────────────────
# 16 preguntas situacionales de programación con mapeo VARK interno.
# Las opciones están mezcladas intencionalmente (no siempre V primero).

PREGUNTAS_ESTATICAS = [
    {
        "id": 1,
        "enunciado": "Cuando aprendes sobre un nuevo algoritmo de ordenamiento, ¿cuál estrategia te resulta más efectiva?",
        "opciones": [
            {"id": "a", "texto": "Ver una animación que muestre cómo se mueven los elementos paso a paso", "estilo": "V"},
            {"id": "b", "texto": "Implementarlo directamente en código y probar con distintos arreglos", "estilo": "K"},
            {"id": "c", "texto": "Escuchar a un profesor o video explicar el proceso verbalmente", "estilo": "A"},
            {"id": "d", "texto": "Leer la definición formal y los pasos escritos del algoritmo", "estilo": "R"},
        ],
    },
    {
        "id": 2,
        "enunciado": "Tienes que aprender a usar una nueva librería de Python. ¿Por dónde empiezas?",
        "opciones": [
            {"id": "a", "texto": "Leer detenidamente la documentación oficial", "estilo": "R"},
            {"id": "b", "texto": "Buscar un diagrama de la arquitectura de la librería", "estilo": "V"},
            {"id": "c", "texto": "Clonar un repositorio de ejemplo y modificar el código directamente", "estilo": "K"},
            {"id": "d", "texto": "Buscar un podcast o video tutorial explicativo", "estilo": "A"},
        ],
    },
    {
        "id": 3,
        "enunciado": "¿Cómo prefieres tomar apuntes cuando estudias programación?",
        "opciones": [
            {"id": "a", "texto": "Grabar audio de las explicaciones para escucharlas después", "estilo": "A"},
            {"id": "b", "texto": "Dibujar diagramas de flujo y mapas conceptuales", "estilo": "V"},
            {"id": "c", "texto": "Crear mini proyectos mientras aprendo para practicar lo que veo", "estilo": "K"},
            {"id": "d", "texto": "Escribir resúmenes detallados con definiciones y ejemplos escritos", "estilo": "R"},
        ],
    },
    {
        "id": 4,
        "enunciado": "Cuando encuentras un bug difícil en tu código, ¿qué haces primero?",
        "opciones": [
            {"id": "a", "texto": "Agregar prints o breakpoints y probar hasta encontrar el origen", "estilo": "K"},
            {"id": "b", "texto": "Revisar la documentación y buscar respuestas en foros escritos", "estilo": "R"},
            {"id": "c", "texto": "Dibujar el flujo de datos del programa para visualizar el problema", "estilo": "V"},
            {"id": "d", "texto": "Explicar el problema en voz alta, ya sea a alguien o a ti mismo", "estilo": "A"},
        ],
    },
    {
        "id": 5,
        "enunciado": "¿Qué tipo de recurso de programación disfrutas más al estudiar?",
        "opciones": [
            {"id": "a", "texto": "Libros técnicos, artículos académicos o tutoriales escritos detallados", "estilo": "R"},
            {"id": "b", "texto": "Desafíos de código (challenges) donde practiques resolviendo problemas", "estilo": "K"},
            {"id": "c", "texto": "Infografías y cheat sheets visuales con colores y estructura clara", "estilo": "V"},
            {"id": "d", "texto": "Podcasts técnicos o clases en video con explicación verbal", "estilo": "A"},
        ],
    },
    {
        "id": 6,
        "enunciado": "Cuando preparas una presentación de tu proyecto de software, ¿cómo lo organizas?",
        "opciones": [
            {"id": "a", "texto": "Ensayando varias veces la explicación verbal del proyecto", "estilo": "A"},
            {"id": "b", "texto": "Mostrando una demo en vivo donde el sistema funciona en tiempo real", "estilo": "K"},
            {"id": "c", "texto": "Con muchos diagramas, capturas de pantalla y elementos visuales", "estilo": "V"},
            {"id": "d", "texto": "Escribiendo un informe técnico detallado con toda la documentación", "estilo": "R"},
        ],
    },
    {
        "id": 7,
        "enunciado": "Estás aprendiendo el concepto de recursividad. ¿Cuál de estos enfoques te ayudaría más?",
        "opciones": [
            {"id": "a", "texto": "Escribir tu propia función recursiva y trazar manualmente los pasos", "estilo": "K"},
            {"id": "b", "texto": "Ver un árbol de llamadas dibujado que muestre cómo se expande la recursión", "estilo": "V"},
            {"id": "c", "texto": "Leer múltiples ejemplos escritos de funciones recursivas con explicación", "estilo": "R"},
            {"id": "d", "texto": "Escuchar a alguien narrar el proceso recursivo paso a paso", "estilo": "A"},
        ],
    },
    {
        "id": 8,
        "enunciado": "¿Cómo prefieres que sea un curso de estructuras de datos?",
        "opciones": [
            {"id": "a", "texto": "Con clases magistrales donde el profesor explica oralmente cada estructura", "estilo": "A"},
            {"id": "b", "texto": "Con visualizaciones animadas de las operaciones (insertar, eliminar, buscar)", "estilo": "V"},
            {"id": "c", "texto": "Con ejercicios prácticos donde implementes cada estructura desde cero", "estilo": "K"},
            {"id": "d", "texto": "Con material de lectura extenso y referencias bibliográficas para profundizar", "estilo": "R"},
        ],
    },
    {
        "id": 9,
        "enunciado": "Cuando aprendes sobre patrones de diseño de software, ¿qué te resulta más útil?",
        "opciones": [
            {"id": "a", "texto": "Leer sobre el problema que resuelve el patrón y su solución documentada", "estilo": "R"},
            {"id": "b", "texto": "Ver un diagrama UML del patrón con los componentes bien representados", "estilo": "V"},
            {"id": "c", "texto": "Refactorizar un proyecto existente aplicando el patrón para entenderlo", "estilo": "K"},
            {"id": "d", "texto": "Escuchar una explicación en video sobre cuándo y cómo usarlo", "estilo": "A"},
        ],
    },
    {
        "id": 10,
        "enunciado": "¿Cómo prefieres aprender sobre la complejidad algorítmica (Big O)?",
        "opciones": [
            {"id": "a", "texto": "Medir el tiempo de ejecución real de algoritmos con diferentes tamaños de entrada", "estilo": "K"},
            {"id": "b", "texto": "Escuchar explicaciones verbales con analogías y ejemplos del mundo real", "estilo": "A"},
            {"id": "c", "texto": "Leer definiciones matemáticas formales y demostraciones escritas", "estilo": "R"},
            {"id": "d", "texto": "Ver gráficas que comparen visualmente las curvas de complejidad", "estilo": "V"},
        ],
    },
    {
        "id": 11,
        "enunciado": "Cuando trabajas en equipo en un proyecto de código, ¿cómo te comunicas mejor?",
        "opciones": [
            {"id": "a", "texto": "Con diagramas de arquitectura y tableros visuales (Kanban, diagramas de flujo)", "estilo": "V"},
            {"id": "b", "texto": "Haciendo pair programming o compartiendo pantalla mientras codifican juntos", "estilo": "K"},
            {"id": "c", "texto": "A través de documentación escrita detallada, comentarios en código y wikis", "estilo": "R"},
            {"id": "d", "texto": "En reuniones verbales o llamadas donde discutan las decisiones", "estilo": "A"},
        ],
    },
    {
        "id": 12,
        "enunciado": "¿Qué te ayuda más cuando intentas memorizar la sintaxis de un lenguaje de programación nuevo?",
        "opciones": [
            {"id": "a", "texto": "Repetir en voz alta la sintaxis o escuchar ejemplos pronunciados", "estilo": "A"},
            {"id": "b", "texto": "Una tarjeta de referencia visual (cheat sheet) con colores y secciones claras", "estilo": "V"},
            {"id": "c", "texto": "Escribir muchos pequeños programas que usen esa sintaxis constantemente", "estilo": "K"},
            {"id": "d", "texto": "Escribir repetidamente la sintaxis en papel o en apuntes detallados", "estilo": "R"},
        ],
    },
    {
        "id": 13,
        "enunciado": "Cuando estudias bases de datos, ¿qué enfoque prefieres?",
        "opciones": [
            {"id": "a", "texto": "Crear una base de datos real e insertar, consultar y modificar datos directamente", "estilo": "K"},
            {"id": "b", "texto": "Ver el diagrama entidad-relación (ER) y el modelo físico de la base de datos", "estilo": "V"},
            {"id": "c", "texto": "Escuchar explicaciones sobre por qué se diseña la base de datos de cierta manera", "estilo": "A"},
            {"id": "d", "texto": "Leer libros sobre normalización, álgebra relacional y documentación SQL", "estilo": "R"},
        ],
    },
    {
        "id": 14,
        "enunciado": "Cuando algo en la clase de programación no te queda claro, ¿qué prefieres hacer?",
        "opciones": [
            {"id": "a", "texto": "Buscar libros, artículos o recursos escritos que expliquen el tema", "estilo": "R"},
            {"id": "b", "texto": "Pedir al profesor que lo dibuje o represente gráficamente en la pizarra", "estilo": "V"},
            {"id": "c", "texto": "Intentar resolverlo tú mismo con un ejercicio práctico hasta que funcione", "estilo": "K"},
            {"id": "d", "texto": "Preguntar al profesor que lo explique de nuevo verbalmente con palabras distintas", "estilo": "A"},
        ],
    },
    {
        "id": 15,
        "enunciado": "¿Cómo prefieres revisar tu progreso cuando estudias un tema de programación?",
        "opciones": [
            {"id": "a", "texto": "Explicar lo aprendido a alguien (amigo, compañero) para verificar tu comprensión", "estilo": "A"},
            {"id": "b", "texto": "Resolver un ejercicio de mayor dificultad para comprobar que lo dominas", "estilo": "K"},
            {"id": "c", "texto": "Releer tus apuntes escritos y comparar con los objetivos del curso", "estilo": "R"},
            {"id": "d", "texto": "Ver una barra de progreso visual o un mapa de los temas dominados", "estilo": "V"},
        ],
    },
    {
        "id": 16,
        "enunciado": "Si tuvieras que aprender a hacer peticiones a una API REST, ¿qué recurso usarías primero?",
        "opciones": [
            {"id": "a", "texto": "La documentación oficial de la API con todos los endpoints y parámetros descritos", "estilo": "R"},
            {"id": "b", "texto": "Usar Postman o escribir código Python para hacer peticiones reales y ver respuestas", "estilo": "K"},
            {"id": "c", "texto": "Un diagrama que ilustre visualmente el ciclo request-response y los códigos HTTP", "estilo": "V"},
            {"id": "d", "texto": "Un video explicativo donde alguien narre cómo funciona una API con ejemplos", "estilo": "A"},
        ],
    },
]


# ─── Generación via Groq ──────────────────────────────────────────────────────

PROMPT_GROQ = """Eres un experto en estilos de aprendizaje VARK (Visual, Auditivo, Lectura/Escritura, Kinestésico).

Genera exactamente {cantidad} preguntas situacionales en español para evaluar el estilo de aprendizaje de estudiantes universitarios de programación.

Reglas:
- Cada pregunta debe tener exactamente 4 opciones, una por cada estilo: V (Visual), A (Auditivo), R (Lectura/Escritura), K (Kinestésico).
- El orden de las opciones dentro de cada pregunta debe ser ALEATORIO (no siempre V primero).
- Las preguntas deben ser situacionales: "¿Qué harías cuando...?" o "¿Cómo prefieres...?"
- Contexto temático: {contexto}
- Todo en español.

Responde ÚNICAMENTE con el JSON válido, sin texto adicional, sin bloques de código markdown, con esta estructura exacta:
{{
  "preguntas": [
    {{
      "id": 1,
      "enunciado": "texto de la pregunta",
      "opciones": [
        {{"id": "a", "texto": "texto de la opción", "estilo": "K"}},
        {{"id": "b", "texto": "texto de la opción", "estilo": "V"}},
        {{"id": "c", "texto": "texto de la opción", "estilo": "R"}},
        {{"id": "d", "texto": "texto de la opción", "estilo": "A"}}
      ]
    }}
  ]
}}"""


def generar_test_vark():
    """
    Genera el test VARK que verá el estudiante, respetando la configuración
    que definió el administrador (Fase 3).

    - modo == 'banco_fijo'  → muestrea preguntas aprobadas del banco.
    - modo == 'dinamico_ia' → genera con Groq; si falla, cae al banco y luego al estático.

    Returns:
        tuple: (lista_de_preguntas, fuente)  donde fuente ∈ {'groq', 'banco', 'estatico'}
    """
    config = _get_config()
    num = config['num_preguntas'] if config else 15
    contexto = config['contexto_tematico'] if config else ''
    modo = config['modo'] if config else 'dinamico_ia'
    usar_fallback = config['usar_fallback'] if config else True

    if modo == 'banco_fijo':
        preguntas = _muestrear_banco(num)
        if preguntas:
            return preguntas, 'banco'
        # Banco vacío: si hay fallback, usamos el estático
        if usar_fallback:
            return _muestrear_estatico(num), 'estatico'
        return _muestrear_estatico(num), 'estatico'

    # modo dinámico (IA)
    try:
        return _generar_via_groq(num, contexto)
    except Exception as exc:
        logger.warning('Groq no disponible para el test. Razón: %s', exc)
        if usar_fallback:
            preguntas = _muestrear_banco(num)
            if preguntas:
                return preguntas, 'banco'
        return _muestrear_estatico(num), 'estatico'


def _get_config():
    """Lee la configuración singleton sin romper si la tabla aún no existe."""
    try:
        from apps.accounts.models import ConfiguracionTestVARK
        c = ConfiguracionTestVARK.get_solo()
        return {
            'modo': c.modo,
            'num_preguntas': c.num_preguntas,
            'contexto_tematico': c.contexto_tematico,
            'usar_fallback': c.usar_fallback,
        }
    except Exception:
        return None


def _muestrear_estatico(num):
    """Toma `num` preguntas del banco estático y reindexa los ids a 1..num."""
    import random
    seleccion = list(PREGUNTAS_ESTATICAS)
    random.shuffle(seleccion)
    seleccion = seleccion[:num] if num else seleccion
    resultado = []
    for i, p in enumerate(seleccion, start=1):
        resultado.append({
            'id': i,
            'enunciado': p['enunciado'],
            'opciones': [dict(o) for o in p['opciones']],
        })
    return resultado


def _muestrear_banco(num):
    """Muestrea preguntas activas del banco oficial (Fase 3). [] si está vacío."""
    import random
    try:
        from apps.accounts.models import PreguntaVARK
    except Exception:
        return []
    qs = list(PreguntaVARK.objects.filter(activo=True).prefetch_related('opciones'))
    if not qs:
        return []
    random.shuffle(qs)
    qs = qs[:num] if num else qs
    resultado = []
    for i, p in enumerate(qs, start=1):
        opciones = list(p.opciones.all())
        if len(opciones) < 4:
            continue
        random.shuffle(opciones)
        resultado.append({
            'id': i,
            'enunciado': p.enunciado,
            'opciones': [
                {'id': chr(ord('a') + j), 'texto': o.texto, 'estilo': o.estilo}
                for j, o in enumerate(opciones)
            ],
        })
    return resultado


def generar_preguntas_candidatas(cantidad=10, contexto=''):
    """
    Forma A (Fase 3): genera preguntas candidatas con IA para que el admin las
    revise/edite/apruebe. NO las guarda en el banco. Si la IA falla y se permite,
    devuelve candidatas tomadas del banco estático como respaldo.

    Returns:
        tuple: (lista_candidatas, fuente)  fuente ∈ {'groq', 'estatico'}
    """
    cantidad = max(5, min(20, cantidad))
    try:
        preguntas, _ = _generar_via_groq(cantidad, contexto)
        return preguntas, 'groq'
    except Exception as exc:
        logger.warning('Groq no disponible para candidatas. Razón: %s', exc)
        return _muestrear_estatico(cantidad), 'estatico'


def _generar_via_groq(cantidad=15, contexto=''):
    from groq import Groq

    cantidad = max(12, min(20, cantidad))
    prompt = PROMPT_GROQ.format(
        cantidad=cantidad,
        contexto=contexto or 'aprender conceptos de programación (algoritmos, estructuras de datos, POO, etc.)',
    )

    client = Groq(api_key=settings.GROQ_API_KEY)

    response = client.chat.completions.create(
        model=settings.GROQ_MODEL,
        messages=[{'role': 'user', 'content': prompt}],
        temperature=0.7,
        max_tokens=4000,
    )

    content = response.choices[0].message.content.strip()

    # Remover bloques markdown si el modelo los incluye
    if '```json' in content:
        content = content.split('```json')[1].split('```')[0].strip()
    elif '```' in content:
        content = content.split('```')[1].split('```')[0].strip()

    data = json.loads(content)
    preguntas = data.get('preguntas', [])

    if len(preguntas) < 12:
        raise ValueError(f'Groq retornó {len(preguntas)} preguntas (mínimo 12).')

    # Validar que cada pregunta tenga las 4 opciones con estilo
    estilos_validos = {'V', 'A', 'R', 'K'}
    for p in preguntas:
        estilos = {o['estilo'] for o in p.get('opciones', [])}
        if not estilos_validos.issubset(estilos):
            raise ValueError(f'Pregunta {p.get("id")} no tiene los 4 estilos VARK.')

    return preguntas, 'groq'


# ─── Cálculo del vector VARK ──────────────────────────────────────────────────

def calcular_vector_vark(preguntas, respuestas):
    """
    Calcula el vector VARK normalizado a partir de las respuestas del estudiante.

    Args:
        preguntas: list — preguntas con opciones que incluyen el campo 'estilo'
        respuestas: dict — {str(pregunta_id): opcion_id}, ej: {"1": "b", "2": "d"}

    Returns:
        dict — {'V': float, 'A': float, 'R': float, 'K': float} (suma = 1.0)
    """
    conteo = {'V': 0, 'A': 0, 'R': 0, 'K': 0}

    for pregunta in preguntas:
        pregunta_id = str(pregunta['id'])
        opcion_elegida = respuestas.get(pregunta_id)
        if not opcion_elegida:
            continue
        for opcion in pregunta['opciones']:
            if opcion['id'] == opcion_elegida:
                estilo = opcion.get('estilo')
                if estilo in conteo:
                    conteo[estilo] += 1
                break

    total = sum(conteo.values())
    if total == 0:
        return {'V': 0.25, 'A': 0.25, 'R': 0.25, 'K': 0.25}

    return {k: round(v / total, 4) for k, v in conteo.items()}
