from django.contrib import admin

from .models import (
    OpcionPregunta,
    Pregunta,
    Recurso,
    ResultadoQuiz,
    Subtema,
    SugerenciaIA,
    Tema,
)


class SubtemaInline(admin.TabularInline):
    model = Subtema
    extra = 1
    fields = ['nombre', 'descripcion', 'orden', 'activo']


@admin.register(Tema)
class TemaAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'orden', 'activo']
    list_editable = ['orden', 'activo']
    search_fields = ['nombre']
    inlines = [SubtemaInline]


@admin.register(Subtema)
class SubtemaAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'tema', 'orden', 'activo']
    list_filter = ['tema', 'activo']
    search_fields = ['nombre', 'tema__nombre']


@admin.register(Recurso)
class RecursoAdmin(admin.ModelAdmin):
    list_display = [
        'titulo', 'tema', 'categoria_vark', 'nivel_complejidad',
        'tipo_formato', 'activo', 'url_valida', 'sugerido_por_ia',
    ]
    list_filter = ['categoria_vark', 'nivel_complejidad', 'tipo_formato', 'activo', 'url_valida', 'sugerido_por_ia']
    search_fields = ['titulo', 'descripcion']
    readonly_fields = ['url_valida', 'ultima_verificacion', 'fecha_creacion', 'fecha_actualizacion']
    raw_id_fields = ['creado_por', 'validado_por', 'tema', 'subtema']


@admin.register(SugerenciaIA)
class SugerenciaIAAdmin(admin.ModelAdmin):
    list_display = ['titulo', 'tema', 'categoria_vark', 'estado', 'fecha_sugerencia', 'revisado_por']
    list_filter = ['estado', 'categoria_vark', 'tema']
    readonly_fields = ['fecha_sugerencia', 'fecha_revision']
    raw_id_fields = ['revisado_por', 'recurso_creado']


class OpcionPreguntaInline(admin.TabularInline):
    model = OpcionPregunta
    extra = 4
    fields = ['texto', 'es_correcta']


@admin.register(Pregunta)
class PreguntaAdmin(admin.ModelAdmin):
    list_display = ['enunciado_corto', 'tema', 'nivel_dificultad', 'activo']
    list_filter = ['tema', 'nivel_dificultad', 'activo']
    search_fields = ['enunciado']
    inlines = [OpcionPreguntaInline]
    raw_id_fields = ['creado_por', 'subtema']

    def enunciado_corto(self, obj):
        return obj.enunciado[:80] + '...' if len(obj.enunciado) > 80 else obj.enunciado
    enunciado_corto.short_description = 'Enunciado'


@admin.register(ResultadoQuiz)
class ResultadoQuizAdmin(admin.ModelAdmin):
    list_display = ['estudiante', 'tema', 'puntaje', 'respuestas_correctas', 'total_preguntas', 'fecha_realizacion']
    list_filter = ['tema']
    readonly_fields = ['fecha_realizacion']
    raw_id_fields = ['estudiante']
