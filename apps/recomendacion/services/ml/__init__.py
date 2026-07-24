"""
Módulo de Machine Learning real (scikit-learn) para el motor de recomendación.

- dataset.py   → construye el dataset etiquetado desde la BD.
- train.py     → entrena KMeans (no supervisado) + clasificador de utilidad (supervisado).
- inference.py → carga los modelos y expone predicción/cluster con fallback seguro.
"""
