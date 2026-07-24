from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import PerfilVARK, SesionTestVARK, Usuario


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    ordering = ['email']
    list_display = ['email', 'nombre', 'apellido', 'rol', 'is_active', 'fecha_registro']
    list_filter = ['rol', 'is_active', 'is_staff']
    search_fields = ['email', 'nombre', 'apellido']
    filter_horizontal = ['groups', 'user_permissions']

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Información personal', {'fields': ('nombre', 'apellido', 'rol')}),
        ('Permisos', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Fechas', {'fields': ('fecha_registro', 'last_login')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'nombre', 'apellido', 'rol', 'password1', 'password2'),
        }),
    )
    readonly_fields = ['fecha_registro', 'last_login']


@admin.register(PerfilVARK)
class PerfilVARKAdmin(admin.ModelAdmin):
    list_display = [
        'usuario', 'puntaje_visual', 'puntaje_auditivo',
        'puntaje_lectura', 'puntaje_kinestesico', 'test_completado', 'fecha_test',
    ]
    list_filter = ['test_completado']
    search_fields = ['usuario__email', 'usuario__nombre']
    readonly_fields = ['fecha_test']


@admin.register(SesionTestVARK)
class SesionTestVARKAdmin(admin.ModelAdmin):
    list_display = ['usuario', 'completado', 'creado_en']
    list_filter = ['completado']
    search_fields = ['usuario__email']
    readonly_fields = ['creado_en']
