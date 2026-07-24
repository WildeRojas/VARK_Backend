from django.contrib import admin

from .models import (
    ConfiguracionMotor,
    EventoClickstream,
    HistorialPerfilVARK,
    Recomendacion,
    ValoracionRecurso,
)


@admin.register(EventoClickstream)
class EventoClickstreamAdmin(admin.ModelAdmin):
    list_display = ['estudiante', 'recurso', 'tipo_evento', 'duracion_segundos', 'timestamp', 'procesado']
    list_filter = ['tipo_evento', 'procesado']
    readonly_fields = ['timestamp']
    raw_id_fields = ['estudiante', 'recurso']
    date_hierarchy = 'timestamp'


@admin.register(ValoracionRecurso)
class ValoracionRecursoAdmin(admin.ModelAdmin):
    list_display = ['estudiante', 'recurso', 'valoracion', 'fecha']
    list_filter = ['valoracion']
    readonly_fields = ['fecha']
    raw_id_fields = ['estudiante', 'recurso']


@admin.register(Recomendacion)
class RecomendacionAdmin(admin.ModelAdmin):
    list_display = ['estudiante', 'recurso', 'tema', 'puntuacion', 'vista', 'fecha_recomendacion']
    list_filter = ['tema', 'vista']
    readonly_fields = ['fecha_recomendacion', 'vector_vark_snapshot']
    raw_id_fields = ['estudiante', 'recurso']
    date_hierarchy = 'fecha_recomendacion'


@admin.register(HistorialPerfilVARK)
class HistorialPerfilVARKAdmin(admin.ModelAdmin):
    list_display = ['estudiante', 'origen', 'fecha']
    list_filter = ['origen']
    readonly_fields = ['fecha', 'vector_anterior', 'vector_nuevo']
    raw_id_fields = ['estudiante']
    date_hierarchy = 'fecha'


@admin.register(ConfiguracionMotor)
class ConfiguracionMotorAdmin(admin.ModelAdmin):
    list_display = [
        'factor_decaimiento', 'umbral_similitud', 'max_recomendaciones',
        'peso_valoracion_util', 'dias_ventana_clickstream', 'actualizado_en',
    ]
    readonly_fields = ['actualizado_en']

    def has_add_permission(self, request):
        return not ConfiguracionMotor.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False

