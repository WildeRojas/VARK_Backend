from django.urls import path

from .views import (
    CambiarPasswordView,
    LoginView,
    LogoutView,
    MeView,
    PerfilVARKView,
    RegistroView,
    ResetPasswordView,
    UsuarioDetailView,
    UsuarioListCreateView,
    VARKBancoDetailView,
    VARKBancoListCreateView,
    VARKCompletarTestView,
    VARKConfigView,
    VARKGenerarPreguntasView,
    VARKGenerarTestView,
    VARKPreviewView,
)

urlpatterns = [
    # CU-01: Registro
    path('registro/', RegistroView.as_view(), name='accounts-registro'),

    # CU-02: Autenticación
    path('login/', LoginView.as_view(), name='accounts-login'),
    path('logout/', LogoutView.as_view(), name='accounts-logout'),
    path('me/', MeView.as_view(), name='accounts-me'),
    path('me/cambiar-password/', CambiarPasswordView.as_view(), name='accounts-cambiar-password'),

    # CU-03: Test VARK
    path('vark/test/', VARKGenerarTestView.as_view(), name='vark-generar'),
    path('vark/completar/', VARKCompletarTestView.as_view(), name='vark-completar'),
    path('vark/perfil/', PerfilVARKView.as_view(), name='vark-perfil'),

    # Fase 3: Edición del test VARK por el Administrador
    path('vark/config/', VARKConfigView.as_view(), name='vark-config'),
    path('vark/generar-preguntas/', VARKGenerarPreguntasView.as_view(), name='vark-generar-preguntas'),
    path('vark/banco/', VARKBancoListCreateView.as_view(), name='vark-banco'),
    path('vark/banco/<int:pk>/', VARKBancoDetailView.as_view(), name='vark-banco-detail'),
    path('vark/preview/', VARKPreviewView.as_view(), name='vark-preview'),

    # Fase 2: Gestión de usuarios (Administrador)
    path('usuarios/', UsuarioListCreateView.as_view(), name='usuario-list-create'),
    path('usuarios/<int:pk>/', UsuarioDetailView.as_view(), name='usuario-detail'),
    path('usuarios/<int:pk>/reset-password/', ResetPasswordView.as_view(), name='usuario-reset-password'),
]
