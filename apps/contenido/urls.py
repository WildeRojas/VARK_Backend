from django.urls import path

from django.urls import path

from .views import (
    PreguntaDetailView,
    PreguntaListCreateView,
    QuizHistorialView,
    QuizObtenerPreguntasView,
    QuizResponderView,
    RecursoDetailView,
    RecursoListCreateView,
    SubtemaListCreateView,
    SugerenciaIAAprobarView,
    SugerenciaIAListView,
    SugerenciaIARechazarView,
    SugerirPreguntasIAView,
    SugerirRecursosIAView,
    TemaDetailView,
    TemaListCreateView,
)

urlpatterns = [
    # CU-04: Temas y subtemas
    path('temas/', TemaListCreateView.as_view(), name='tema-list-create'),
    path('temas/<int:pk>/', TemaDetailView.as_view(), name='tema-detail'),
    path('temas/<int:tema_pk>/subtemas/', SubtemaListCreateView.as_view(), name='subtema-list-create'),

    # CU-08 / CU-11: Recursos académicos (con filtros VARK/tema/nivel)
    path('recursos/', RecursoListCreateView.as_view(), name='recurso-list-create'),
    path('recursos/<int:pk>/', RecursoDetailView.as_view(), name='recurso-detail'),

    # CU-09: Solicitar sugerencias de recursos via IA
    path('recursos/sugerir/', SugerirRecursosIAView.as_view(), name='sugerir-recursos-ia'),

    # CU-10: Gestionar sugerencias IA (pendientes, aprobar, rechazar)
    path('sugerencias/', SugerenciaIAListView.as_view(), name='sugerencia-list'),
    path('sugerencias/<int:pk>/aprobar/', SugerenciaIAAprobarView.as_view(), name='sugerencia-aprobar'),
    path('sugerencias/<int:pk>/rechazar/', SugerenciaIARechazarView.as_view(), name='sugerencia-rechazar'),

    # CU-05: Banco de preguntas
    path('preguntas/', PreguntaListCreateView.as_view(), name='pregunta-list-create'),
    path('preguntas/sugerir/', SugerirPreguntasIAView.as_view(), name='pregunta-sugerir-ia'),
    path('preguntas/<int:pk>/', PreguntaDetailView.as_view(), name='pregunta-detail'),

    # CU-07: Quizzes
    path('quiz/<int:tema_pk>/preguntas/', QuizObtenerPreguntasView.as_view(), name='quiz-preguntas'),
    path('quiz/responder/', QuizResponderView.as_view(), name='quiz-responder'),
    path('quiz/historial/', QuizHistorialView.as_view(), name='quiz-historial'),
]
