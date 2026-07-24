from django.urls import path

from django.urls import path

from .views import (
    ConfiguracionMotorView,
    HistorialPerfilVARKView,
    MarcarRecomendacionVistaView,
    MLEstadoView,
    RecomendarRecursosView,
    RecomendacionHistorialView,
    RegistrarEventoClickstreamView,
    ValoracionRecursoView,
)

urlpatterns = [
    # CU-12 / CU-13: Motor de recomendación CBF
    path('recomendar/', RecomendarRecursosView.as_view(), name='recomendar'),
    path('mis-recomendaciones/', RecomendacionHistorialView.as_view(), name='recomendacion-historial'),
    path('<int:pk>/vista/', MarcarRecomendacionVistaView.as_view(), name='recomendacion-vista'),

    # CU-15: Clickstream
    path('clickstream/', RegistrarEventoClickstreamView.as_view(), name='clickstream'),

    # CU-14: Valoraciones
    path('valoraciones/', ValoracionRecursoView.as_view(), name='valoracion'),

    # CU-16: Historial evolución del perfil VARK
    path('perfil/historial/', HistorialPerfilVARKView.as_view(), name='historial-perfil-vark'),

    # CU-06: Configuración del motor (Admin)
    path('configuracion/', ConfiguracionMotorView.as_view(), name='configuracion-motor'),

    # Fase 5: Estado del modelo de ML
    path('ml/estado/', MLEstadoView.as_view(), name='ml-estado'),
]

