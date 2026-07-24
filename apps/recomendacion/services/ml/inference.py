"""
Inferencia con los modelos entrenados. Carga perezosa + caché en memoria.

Todo está protegido con fallback: si no hay modelo o falla la carga, las funciones
devuelven valores neutros para que el motor siga funcionando solo con CBF.
"""

import json
import os

from .dataset import construir_features, fila_features_ordenada
from .train import CLF_PATH, CLUSTER_PATH, METRICS_PATH

_CACHE = {'clf': None, 'cluster': None, 'clf_mtime': None, 'cluster_mtime': None}


def modelo_disponible():
    return os.path.exists(CLF_PATH)


def _cargar_clf():
    """Carga (o recarga si cambió en disco) el clasificador. Devuelve dict o None."""
    if not os.path.exists(CLF_PATH):
        return None
    mtime = os.path.getmtime(CLF_PATH)
    if _CACHE['clf'] is None or _CACHE['clf_mtime'] != mtime:
        try:
            import joblib
            _CACHE['clf'] = joblib.load(CLF_PATH)
            _CACHE['clf_mtime'] = mtime
        except Exception:
            _CACHE['clf'] = None
    return _CACHE['clf']


def _cargar_cluster():
    if not os.path.exists(CLUSTER_PATH):
        return None
    mtime = os.path.getmtime(CLUSTER_PATH)
    if _CACHE['cluster'] is None or _CACHE['cluster_mtime'] != mtime:
        try:
            import joblib
            _CACHE['cluster'] = joblib.load(CLUSTER_PATH)
            _CACHE['cluster_mtime'] = mtime
        except Exception:
            _CACHE['cluster'] = None
    return _CACHE['cluster']


def predecir_utilidad(vark, categoria_vark, nivel_complejidad, tipo_formato, clics=0, permanencia=0):
    """
    Probabilidad (0–1) de que el recurso sea útil para el estudiante.
    Devuelve None si no hay modelo (el caller usa solo CBF).
    """
    bundle = _cargar_clf()
    if not bundle:
        return None
    try:
        import numpy as np
        feat = construir_features(
            vark, categoria_vark, nivel_complejidad, tipo_formato, clics, permanencia
        )
        x = np.array([fila_features_ordenada(feat)], dtype=float)
        clf = bundle['clf']
        # Índice de la clase positiva (1)
        clases = list(clf.classes_)
        idx = clases.index(1) if 1 in clases else len(clases) - 1
        return float(clf.predict_proba(x)[0][idx])
    except Exception:
        return None


def cluster_de(vark, total_clics=0, permanencia_media=0.0, quiz_medio=0.0):
    """Devuelve el id de cluster del estudiante, o None si no hay modelo de cluster."""
    bundle = _cargar_cluster()
    if not bundle:
        return None
    try:
        import numpy as np
        fila = [
            vark.get('V', 0.0), vark.get('A', 0.0), vark.get('R', 0.0), vark.get('K', 0.0),
            total_clics, permanencia_media, quiz_medio,
        ]
        x = bundle['scaler'].transform(np.array([fila], dtype=float))
        return int(bundle['kmeans'].predict(x)[0])
    except Exception:
        return None


def cargar_metricas():
    """Devuelve el dict de métricas del último entrenamiento, o None."""
    if not os.path.exists(METRICS_PATH):
        return None
    try:
        with open(METRICS_PATH, encoding='utf-8') as fh:
            return json.load(fh)
    except Exception:
        return None
