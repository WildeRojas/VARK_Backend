from rest_framework import serializers

from .models import (
    ConfiguracionMotor,
    EventoClickstream,
    HistorialPerfilVARK,
    Recomendacion,
    ValoracionRecurso,
)


# ─── CU-15: Clickstream ───────────────────────────────────────────────────────

class EventoClickstreamSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventoClickstream
        fields = ['id', 'recurso', 'tipo_evento', 'duracion_segundos', 'timestamp']
        read_only_fields = ['id', 'timestamp']

    def validate_duracion_segundos(self, value):
        if value is not None and value < 0:
            raise serializers.ValidationError('La duración no puede ser negativa.')
        return value


# ─── CU-14: Valoraciones ─────────────────────────────────────────────────────

class ValoracionRecursoSerializer(serializers.ModelSerializer):
    recurso_titulo = serializers.ReadOnlyField(source='recurso.titulo')

    class Meta:
        model = ValoracionRecurso
        fields = ['id', 'recurso', 'recurso_titulo', 'valoracion', 'comentario', 'fecha']
        read_only_fields = ['id', 'fecha']


# ─── CU-12 / CU-13: Recomendaciones ─────────────────────────────────────────

class RecomendacionSerializer(serializers.ModelSerializer):
    recurso_titulo = serializers.ReadOnlyField(source='recurso.titulo')
    recurso_url = serializers.ReadOnlyField(source='recurso.url')
    recurso_tipo = serializers.ReadOnlyField(source='recurso.tipo_formato')
    recurso_tipo_display = serializers.ReadOnlyField(source='recurso.get_tipo_formato_display')
    recurso_categoria_vark = serializers.ReadOnlyField(source='recurso.categoria_vark')
    recurso_nivel = serializers.ReadOnlyField(source='recurso.nivel_complejidad')
    tema_nombre = serializers.ReadOnlyField(source='tema.nombre')

    class Meta:
        model = Recomendacion
        fields = [
            'id',
            'recurso', 'recurso_titulo', 'recurso_url',
            'recurso_tipo', 'recurso_tipo_display',
            'recurso_categoria_vark', 'recurso_nivel',
            'tema', 'tema_nombre',
            'puntuacion', 'justificacion',
            'vector_vark_snapshot',
            'fecha_recomendacion', 'vista',
        ]
        read_only_fields = fields


class SolicitarRecomendacionSerializer(serializers.Serializer):
    tema_id = serializers.IntegerField()
    usar_groq = serializers.BooleanField(
        default=False,
        help_text='Si True, genera justificaciones con Groq (más lentas pero personalizadas).',
    )

    def validate_tema_id(self, value):
        from apps.contenido.models import Tema
        if not Tema.objects.filter(pk=value, activo=True).exists():
            raise serializers.ValidationError('Tema no encontrado o inactivo.')
        return value


# ─── CU-16: Historial perfil VARK ────────────────────────────────────────────

class HistorialPerfilVARKSerializer(serializers.ModelSerializer):
    origen_display = serializers.ReadOnlyField(source='get_origen_display')

    class Meta:
        model = HistorialPerfilVARK
        fields = ['id', 'vector_anterior', 'vector_nuevo', 'origen', 'origen_display', 'fecha']
        read_only_fields = fields


# ─── CU-06: Configuración del motor ──────────────────────────────────────────

class ConfiguracionMotorSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConfiguracionMotor
        fields = [
            'factor_decaimiento',
            'umbral_similitud',
            'max_recomendaciones',
            'peso_valoracion_util',
            'dias_ventana_clickstream',
            'peso_cbf',
            'peso_ml',
            'usar_ml',
            'actualizado_en',
        ]
        read_only_fields = ['actualizado_en']

    def validate_factor_decaimiento(self, value):
        if not (0 < value <= 1):
            raise serializers.ValidationError('Debe estar entre 0 (excluido) y 1.')
        return value

    def validate_umbral_similitud(self, value):
        if not (0 <= value <= 1):
            raise serializers.ValidationError('Debe estar entre 0 y 1.')
        return value

    def validate_max_recomendaciones(self, value):
        if value < 1 or value > 50:
            raise serializers.ValidationError('Debe estar entre 1 y 50.')
        return value

    def validate_peso_cbf(self, value):
        if not (0 <= value <= 1):
            raise serializers.ValidationError('Debe estar entre 0 y 1.')
        return value

    def validate_peso_ml(self, value):
        if not (0 <= value <= 1):
            raise serializers.ValidationError('Debe estar entre 0 y 1.')
        return value
