from rest_framework.permissions import BasePermission, SAFE_METHODS


class EsEstudiante(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.rol == 'estudiante'
        )


class EsDocente(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.rol == 'docente'
        )


class EsAdmin(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.rol == 'administrador'
        )


class EsDocenteOAdmin(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.rol in ('docente', 'administrador')
        )


class EsDocenteOAdminOLecturaEstudiante(BasePermission):
    """Lectura para cualquier autenticado; escritura solo docente/admin."""
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if request.method in SAFE_METHODS:
            return True
        return request.user.rol in ('docente', 'administrador')
