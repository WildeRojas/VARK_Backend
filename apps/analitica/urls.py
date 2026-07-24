from django.urls import path

from django.urls import path

from .views import (
    AsignarEstudiantesView,
    DashboardAdminView,
    DashboardEstudianteView,
    EnviarNotificacionNuevoRecursoView,
    ExperimentoABDetailView,
    ExperimentoABListCreateView,
    ExportarReporteView,
    HistorialVARKDetalleView,
    NotificacionListView,
    NotificacionMarcarLeidaView,
    NotificacionMarcarTodasLeidasView,
    Perfil360EstudianteView,
    ReporteDocenteView,
    ResultadosExperimentoView,
)

urlpatterns = [
    # CU-17: Dashboard personal estudiante
    path('dashboard/', DashboardEstudianteView.as_view(), name='dashboard-estudiante'),

    # Fase 2: Dashboard del administrador y vista 360° del estudiante
    path('dashboard/admin/', DashboardAdminView.as_view(), name='dashboard-admin'),
    path('estudiantes/<int:pk>/perfil-360/', Perfil360EstudianteView.as_view(), name='estudiante-perfil-360'),

    # CU-18: Historial detallado de evolución del perfil VARK
    path('perfil/historial-detalle/', HistorialVARKDetalleView.as_view(), name='historial-vark-detalle'),

    # CU-19: Reporte estadístico para docentes
    path('reporte/docente/', ReporteDocenteView.as_view(), name='reporte-docente'),

    # CU-21: Exportar reporte en CSV/PDF
    path('reporte/exportar/', ExportarReporteView.as_view(), name='reporte-exportar'),

    # CU-20: Gestión experimentos A/B
    path('experimentos/', ExperimentoABListCreateView.as_view(), name='experimento-list-create'),
    path('experimentos/<int:pk>/', ExperimentoABDetailView.as_view(), name='experimento-detail'),
    path('experimentos/<int:pk>/asignar/', AsignarEstudiantesView.as_view(), name='experimento-asignar'),
    path('experimentos/<int:pk>/resultados/', ResultadosExperimentoView.as_view(), name='experimento-resultados'),

    # CU-22: Notificaciones
    path('notificaciones/', NotificacionListView.as_view(), name='notificacion-list'),
    path('notificaciones/leer-todas/', NotificacionMarcarTodasLeidasView.as_view(), name='notificacion-leer-todas'),
    path('notificaciones/<int:pk>/leer/', NotificacionMarcarLeidaView.as_view(), name='notificacion-leer'),
    path('notificaciones/nuevo-recurso/', EnviarNotificacionNuevoRecursoView.as_view(), name='notificacion-nuevo-recurso'),
]

