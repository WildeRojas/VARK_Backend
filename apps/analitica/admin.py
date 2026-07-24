from django.contrib import admin

from .models import AsignacionExperimento, ExperimentoAB, Notificacion


class AsignacionExperimentoInline(admin.TabularInline):
    model = AsignacionExperimento
    extra = 0
    fields = ['estudiante', 'grupo', 'fecha_asignacion']
    readonly_fields = ['fecha_asignacion']
    raw_id_fields = ['estudiante']


@admin.register(ExperimentoAB)
class ExperimentoABAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'estado', 'creado_por', 'fecha_inicio', 'fecha_fin']
    list_filter = ['estado']
    readonly_fields = ['fecha_inicio']
    raw_id_fields = ['creado_por']
    inlines = [AsignacionExperimentoInline]


@admin.register(Notificacion)
class NotificacionAdmin(admin.ModelAdmin):
    list_display = ['destinatario', 'tipo', 'titulo', 'leida', 'fecha']
    list_filter = ['tipo', 'leida']
    readonly_fields = ['fecha']
    raw_id_fields = ['destinatario', 'recurso']
    date_hierarchy = 'fecha'

