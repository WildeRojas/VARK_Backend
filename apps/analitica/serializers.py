from rest_framework import serializers

from .models import AsignacionExperimento, ExperimentoAB, Notificacion


# ─── CU-20: Experimento A/B ──────────────────────────────────────────────────

class ExperimentoABSerializer(serializers.ModelSerializer):
    creado_por_email = serializers.ReadOnlyField(source='creado_por.email')
    total_asignados = serializers.SerializerMethodField()

    class Meta:
        model = ExperimentoAB
        fields = [
            'id', 'nombre', 'descripcion', 'estado',
            'creado_por', 'creado_por_email',
            'fecha_inicio', 'fecha_fin',
            'total_asignados',
        ]
        read_only_fields = ['id', 'creado_por', 'fecha_inicio']

    def get_total_asignados(self, obj):
        return obj.asignaciones.count()


class AsignacionExperimentoSerializer(serializers.ModelSerializer):
    estudiante_email = serializers.ReadOnlyField(source='estudiante.email')

    class Meta:
        model = AsignacionExperimento
        fields = ['id', 'experimento', 'estudiante', 'estudiante_email', 'grupo', 'fecha_asignacion']
        read_only_fields = ['id', 'fecha_asignacion']


class AsignarEstudiantesSerializer(serializers.Serializer):
    """Payload para asignar masivamente estudiantes a un experimento."""
    estudiante_ids = serializers.ListField(
        child=serializers.IntegerField(),
        min_length=1,
    )
    grupo = serializers.ChoiceField(choices=['experimental', 'control'])


# ─── CU-22: Notificaciones ───────────────────────────────────────────────────

class NotificacionSerializer(serializers.ModelSerializer):
    tipo_display = serializers.ReadOnlyField(source='get_tipo_display')
    recurso_titulo = serializers.ReadOnlyField(source='recurso.titulo')

    class Meta:
        model = Notificacion
        fields = [
            'id', 'tipo', 'tipo_display', 'titulo', 'mensaje',
            'recurso', 'recurso_titulo', 'leida', 'fecha',
        ]
        read_only_fields = fields


# ─── CU-17: Dashboard (datos sin modelo propio) ──────────────────────────────

class DashboardEstudianteSerializer(serializers.Serializer):
    """Respuesta del endpoint de dashboard personal del estudiante."""
    perfil_vark = serializers.DictField()          # {V, A, R, K} actual
    estilo_dominante = serializers.CharField()
    evolucion_semanal = serializers.ListField()    # [{semana, V, A, R, K}]
    progreso_por_tema = serializers.ListField()    # [{tema, puntaje_promedio, quizzes_realizados}]
    total_recursos_vistos = serializers.IntegerField()
    total_quizzes_realizados = serializers.IntegerField()


# ─── CU-19: Reporte docente (datos sin modelo propio) ────────────────────────

class ReporteDocenteSerializer(serializers.Serializer):
    """Respuesta del endpoint de reporte para docentes."""
    total_estudiantes = serializers.IntegerField()
    promedio_puntaje_quizzes = serializers.FloatField()
    recursos_mas_efectivos = serializers.ListField()
    estudiantes_bajo_engagement = serializers.ListField()
    distribucion_vark = serializers.DictField()    # {V: n, A: n, R: n, K: n}


# ─── CU-21: Export (parámetros de descarga) ──────────────────────────────────

class ExportReporteSerializer(serializers.Serializer):
    formato = serializers.ChoiceField(choices=['csv', 'pdf'], default='csv')
    fecha_inicio = serializers.DateField(required=False)
    fecha_fin = serializers.DateField(required=False)
    tema_id = serializers.IntegerField(required=False)
