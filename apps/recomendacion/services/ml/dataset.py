"""
Construcción del dataset de entrenamiento desde la base de datos.

La unidad de muestra es una **interacción (estudiante, recurso)** etiquetada como
"útil" (1) o "no útil" (0). La etiqueta sale de:
  - ValoracionRecurso explícita ('util' → 1, 'no_util' → 0), o
  - si no hay valoración, una señal implícita del clickstream (permanencia alta → 1).

Las features mezclan el perfil VARK del estudiante con atributos del recurso y el
comportamiento previo (clics / permanencia). El mismo constructor de features se usa
en inferencia para garantizar consistencia.
"""

NIVEL_MAP = {'basico': 0.0, 'intermedio': 1.0, 'avanzado': 2.0}
TIPOS = ['video', 'articulo', 'ejercicio', 'documento']

# Umbral de permanencia (segundos) para considerar "útil" cuando no hay valoración.
UMBRAL_PERMANENCIA_UTIL = 120

# Orden canónico de las columnas de features del clasificador de utilidad.
FEATURE_COLUMNS = (
    ['vark_V', 'vark_A', 'vark_R', 'vark_K', 'afinidad', 'nivel', 'clics', 'permanencia']
    + [f'tipo_{t}' for t in TIPOS]
)

# Columnas para el clustering de estudiantes (no supervisado).
STUDENT_COLUMNS = ['V', 'A', 'R', 'K', 'total_clics', 'permanencia_media', 'quiz_medio']


def construir_features(vark, categoria_vark, nivel_complejidad, tipo_formato, clics=0, permanencia=0):
    """Construye el dict de features de una interacción (estudiante, recurso)."""
    feat = {
        'vark_V': float(vark.get('V', 0.0)),
        'vark_A': float(vark.get('A', 0.0)),
        'vark_R': float(vark.get('R', 0.0)),
        'vark_K': float(vark.get('K', 0.0)),
        'afinidad': float(vark.get(categoria_vark, 0.0)),
        'nivel': NIVEL_MAP.get(nivel_complejidad, 0.0),
        'clics': float(clics),
        'permanencia': float(permanencia),
    }
    for t in TIPOS:
        feat[f'tipo_{t}'] = 1.0 if tipo_formato == t else 0.0
    return feat


def fila_features_ordenada(feat):
    """Devuelve la lista de valores en el orden de FEATURE_COLUMNS."""
    return [feat[c] for c in FEATURE_COLUMNS]


def construir_dataset():
    """
    Returns:
        (X, y, estudiantes_df)
        X: pandas.DataFrame con columnas FEATURE_COLUMNS (interacciones etiquetadas)
        y: pandas.Series 0/1 (útil)
        estudiantes_df: pandas.DataFrame con STUDENT_COLUMNS (uno por estudiante)
    """
    import pandas as pd
    from collections import defaultdict

    from apps.accounts.models import PerfilVARK
    from apps.contenido.models import Recurso, ResultadoQuiz
    from apps.recomendacion.models import EventoClickstream, ValoracionRecurso

    # Perfiles VARK por estudiante
    perfiles = {
        p.usuario_id: p.vector
        for p in PerfilVARK.objects.filter(test_completado=True)
    }

    # Recursos por id (atributos)
    recursos = {
        r.id: r
        for r in Recurso.objects.all()
    }

    # Agregados de clickstream por (estudiante, recurso)
    clics = defaultdict(int)
    permanencia = defaultdict(int)
    for ev in EventoClickstream.objects.all().values(
        'estudiante_id', 'recurso_id', 'tipo_evento', 'duracion_segundos'
    ):
        key = (ev['estudiante_id'], ev['recurso_id'])
        if ev['tipo_evento'] == 'clic':
            clics[key] += 1
        elif ev['tipo_evento'] == 'permanencia':
            permanencia[key] += (ev['duracion_segundos'] or 0)

    # ── Muestras etiquetadas ──────────────────────────────────────────────────
    filas = []
    etiquetas = []
    vistos = set()

    # 1) A partir de valoraciones explícitas
    for val in ValoracionRecurso.objects.all().values(
        'estudiante_id', 'recurso_id', 'valoracion'
    ):
        est_id, rec_id = val['estudiante_id'], val['recurso_id']
        if est_id not in perfiles or rec_id not in recursos:
            continue
        key = (est_id, rec_id)
        vistos.add(key)
        r = recursos[rec_id]
        feat = construir_features(
            perfiles[est_id], r.categoria_vark, r.nivel_complejidad, r.tipo_formato,
            clics.get(key, 0), permanencia.get(key, 0),
        )
        filas.append(feat)
        etiquetas.append(1 if val['valoracion'] == 'util' else 0)

    # 2) A partir de clickstream sin valoración (señal implícita por permanencia)
    for key, perm in permanencia.items():
        if key in vistos:
            continue
        est_id, rec_id = key
        if est_id not in perfiles or rec_id not in recursos:
            continue
        r = recursos[rec_id]
        feat = construir_features(
            perfiles[est_id], r.categoria_vark, r.nivel_complejidad, r.tipo_formato,
            clics.get(key, 0), perm,
        )
        filas.append(feat)
        etiquetas.append(1 if perm >= UMBRAL_PERMANENCIA_UTIL else 0)

    X = pd.DataFrame(filas, columns=FEATURE_COLUMNS) if filas else pd.DataFrame(columns=FEATURE_COLUMNS)
    y = pd.Series(etiquetas, name='util', dtype='int64')

    # ── Dataset de estudiantes para clustering ────────────────────────────────
    quiz_medio = defaultdict(list)
    for q in ResultadoQuiz.objects.all().values('estudiante_id', 'puntaje'):
        quiz_medio[q['estudiante_id']].append(q['puntaje'])

    total_clics_est = defaultdict(int)
    perm_est = defaultdict(list)
    for (est_id, _rec_id), c in clics.items():
        total_clics_est[est_id] += c
    for (est_id, _rec_id), p in permanencia.items():
        perm_est[est_id].append(p)

    est_filas = []
    for est_id, vark in perfiles.items():
        perms = perm_est.get(est_id, [])
        quizzes = quiz_medio.get(est_id, [])
        est_filas.append({
            'V': vark.get('V', 0.0), 'A': vark.get('A', 0.0),
            'R': vark.get('R', 0.0), 'K': vark.get('K', 0.0),
            'total_clics': total_clics_est.get(est_id, 0),
            'permanencia_media': (sum(perms) / len(perms)) if perms else 0.0,
            'quiz_medio': (sum(quizzes) / len(quizzes)) if quizzes else 0.0,
        })

    estudiantes_df = (
        pd.DataFrame(est_filas, columns=STUDENT_COLUMNS)
        if est_filas else pd.DataFrame(columns=STUDENT_COLUMNS)
    )

    return X, y, estudiantes_df
