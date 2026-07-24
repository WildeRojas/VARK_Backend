"""
Entrenamiento de los modelos de ML.

- Supervisado: RandomForestClassifier → probabilidad de que un recurso sea útil
  para un estudiante (reemplaza/complementa la similitud coseno en el ranking).
- No supervisado: KMeans sobre el comportamiento de los estudiantes → segmentación.

Los modelos se guardan con joblib y las métricas en JSON, para mostrarlas en el panel.
"""

import json
import os
from datetime import datetime, timezone

ARTIFACTS_DIR = os.path.join(os.path.dirname(__file__), 'artifacts')
CLF_PATH = os.path.join(ARTIFACTS_DIR, 'clasificador_utilidad.joblib')
CLUSTER_PATH = os.path.join(ARTIFACTS_DIR, 'cluster_estudiantes.joblib')
METRICS_PATH = os.path.join(ARTIFACTS_DIR, 'metricas.json')

MIN_MUESTRAS = 30


def entrenar(test_size=0.25, n_clusters=4, random_state=42):
    """
    Entrena ambos modelos y guarda artefactos + métricas.

    Returns: dict de métricas. Lanza ValueError si no hay datos suficientes.
    """
    import numpy as np
    from sklearn.cluster import KMeans
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.metrics import (
        accuracy_score, confusion_matrix, f1_score, precision_score, recall_score,
        silhouette_score,
    )
    from sklearn.model_selection import train_test_split
    from sklearn.preprocessing import StandardScaler
    import joblib

    from .dataset import FEATURE_COLUMNS, STUDENT_COLUMNS, construir_dataset

    X, y, estudiantes_df = construir_dataset()

    if len(X) < MIN_MUESTRAS:
        raise ValueError(
            f'Datos insuficientes para entrenar: {len(X)} muestras (mínimo {MIN_MUESTRAS}). '
            f'Ejecuta primero "python manage.py seed_ml".'
        )
    if y.nunique() < 2:
        raise ValueError('El dataset tiene una sola clase; se necesitan ejemplos útiles y no útiles.')

    # ── Clasificador de utilidad (supervisado) ────────────────────────────────
    estratificar = y if y.value_counts().min() >= 2 else None
    X_tr, X_te, y_tr, y_te = train_test_split(
        X, y, test_size=test_size, random_state=random_state, stratify=estratificar,
    )
    clf = RandomForestClassifier(
        n_estimators=200, max_depth=8, min_samples_leaf=2,
        random_state=random_state, class_weight='balanced',
    )
    # Entrenamos con arrays (sin nombres de columnas) para que la inferencia con
    # numpy no emita warnings; el orden de FEATURE_COLUMNS se mantiene.
    clf.fit(X_tr.values, y_tr)
    y_pred = clf.predict(X_te.values)

    importancias = dict(zip(FEATURE_COLUMNS, (round(float(v), 4) for v in clf.feature_importances_)))

    clf_metrics = {
        'n_muestras': int(len(X)),
        'n_test': int(len(X_te)),
        'accuracy': round(float(accuracy_score(y_te, y_pred)), 4),
        'precision': round(float(precision_score(y_te, y_pred, zero_division=0)), 4),
        'recall': round(float(recall_score(y_te, y_pred, zero_division=0)), 4),
        'f1': round(float(f1_score(y_te, y_pred, zero_division=0)), 4),
        'matriz_confusion': confusion_matrix(y_te, y_pred).tolist(),
        'importancia_features': importancias,
        'baseline_mayoria': round(float(max(y.mean(), 1 - y.mean())), 4),
    }

    # ── Clustering de estudiantes (no supervisado) ────────────────────────────
    cluster_metrics = {'n_clusters': 0, 'silhouette': None, 'tamanos': [], 'centroides_vark': []}
    scaler = None
    kmeans = None
    if len(estudiantes_df) >= n_clusters and len(estudiantes_df) >= 4:
        k = min(n_clusters, len(estudiantes_df))
        scaler = StandardScaler()
        Xs = scaler.fit_transform(estudiantes_df.values)
        kmeans = KMeans(n_clusters=k, n_init=10, random_state=random_state)
        labels = kmeans.fit_predict(Xs)

        sil = None
        if k >= 2 and len(set(labels)) >= 2:
            sil = round(float(silhouette_score(Xs, labels)), 4)

        tamanos = [int((labels == i).sum()) for i in range(k)]
        # Centroide VARK medio por cluster (en escala original, solo V,A,R,K)
        centroides = []
        for i in range(k):
            sub = estudiantes_df.values[labels == i]
            if len(sub):
                centroides.append({
                    'V': round(float(sub[:, 0].mean()), 3),
                    'A': round(float(sub[:, 1].mean()), 3),
                    'R': round(float(sub[:, 2].mean()), 3),
                    'K': round(float(sub[:, 3].mean()), 3),
                })
            else:
                centroides.append({'V': 0, 'A': 0, 'R': 0, 'K': 0})

        cluster_metrics = {
            'n_clusters': k, 'silhouette': sil,
            'tamanos': tamanos, 'centroides_vark': centroides,
        }

    # ── Guardar artefactos ────────────────────────────────────────────────────
    os.makedirs(ARTIFACTS_DIR, exist_ok=True)
    joblib.dump({'clf': clf, 'columns': list(FEATURE_COLUMNS)}, CLF_PATH)
    if kmeans is not None:
        joblib.dump(
            {'scaler': scaler, 'kmeans': kmeans, 'columns': list(STUDENT_COLUMNS)},
            CLUSTER_PATH,
        )

    metricas = {
        'entrenado_en': datetime.now(timezone.utc).isoformat(),
        'clasificador': clf_metrics,
        'clustering': cluster_metrics,
        'n_estudiantes': int(len(estudiantes_df)),
    }
    with open(METRICS_PATH, 'w', encoding='utf-8') as fh:
        json.dump(metricas, fh, ensure_ascii=False, indent=2)

    return metricas
