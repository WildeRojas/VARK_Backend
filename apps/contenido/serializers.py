from rest_framework import serializers

from .models import (
    OpcionPregunta,
    Pregunta,
    Recurso,
    ResultadoQuiz,
    Subtema,
    SugerenciaIA,
    Tema,
)


# ─── Tema / Subtema (CU-04) ──────────────────────────────────────────────────

class SubtemaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subtema
        fields = ['id', 'nombre', 'descripcion', 'orden', 'activo']


class TemaSerializer(serializers.ModelSerializer):
    subtemas = SubtemaSerializer(many=True, read_only=True)

    class Meta:
        model = Tema
        fields = ['id', 'nombre', 'descripcion', 'orden', 'activo', 'subtemas']


class TemaSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tema
        fields = ['id', 'nombre', 'orden', 'activo']


# ─── Recurso (CU-08, CU-11) ──────────────────────────────────────────────────

class RecursoSerializer(serializers.ModelSerializer):
    tema_nombre = serializers.ReadOnlyField(source='tema.nombre')
    subtema_nombre = serializers.ReadOnlyField(source='subtema.nombre')
    creado_por_email = serializers.ReadOnlyField(source='creado_por.email')
    validado_por_email = serializers.ReadOnlyField(source='validado_por.email')
    categoria_vark_display = serializers.ReadOnlyField(source='get_categoria_vark_display')
    nivel_complejidad_display = serializers.ReadOnlyField(source='get_nivel_complejidad_display')
    tipo_formato_display = serializers.ReadOnlyField(source='get_tipo_formato_display')

    class Meta:
        model = Recurso
        fields = [
            'id', 'titulo', 'url', 'descripcion',
            'tema', 'tema_nombre', 'subtema', 'subtema_nombre',
            'categoria_vark', 'categoria_vark_display',
            'nivel_complejidad', 'nivel_complejidad_display',
            'tipo_formato', 'tipo_formato_display',
            'activo', 'url_valida', 'ultima_verificacion',
            'sugerido_por_ia', 'validado_por', 'validado_por_email',
            'creado_por', 'creado_por_email',
            'fecha_creacion', 'fecha_actualizacion',
        ]
        read_only_fields = [
            'id', 'url_valida', 'ultima_verificacion',
            'sugerido_por_ia', 'validado_por', 'creado_por',
            'fecha_creacion', 'fecha_actualizacion',
        ]

    def validate_url(self, value):
        if not value.startswith(('http://', 'https://')):
            raise serializers.ValidationError('La URL debe comenzar con http:// o https://')
        return value


# ─── Sugerencias IA (CU-09, CU-10) ──────────────────────────────────────────

class SugerenciaIASerializer(serializers.ModelSerializer):
    tema_nombre = serializers.ReadOnlyField(source='tema.nombre')
    revisado_por_email = serializers.ReadOnlyField(source='revisado_por.email')
    estado_display = serializers.ReadOnlyField(source='get_estado_display')

    class Meta:
        model = SugerenciaIA
        fields = [
            'id', 'titulo', 'url', 'descripcion', 'justificacion_pedagogica',
            'tema', 'tema_nombre', 'categoria_vark', 'nivel_complejidad',
            'tipo_formato', 'estado', 'estado_display',
            'revisado_por', 'revisado_por_email', 'recurso_creado',
            'fecha_sugerencia', 'fecha_revision',
        ]
        read_only_fields = [
            'id', 'estado', 'revisado_por', 'recurso_creado',
            'fecha_sugerencia', 'fecha_revision',
        ]


class SolicitarSugerenciaIASerializer(serializers.Serializer):
    tema_id = serializers.IntegerField()
    categoria_vark = serializers.ChoiceField(choices=['V', 'A', 'R', 'K'])
    nivel_complejidad = serializers.ChoiceField(
        choices=['basico', 'intermedio', 'avanzado'], default='basico'
    )
    cantidad = serializers.IntegerField(min_value=5, max_value=10, default=8)

    def validate_tema_id(self, value):
        if not Tema.objects.filter(id=value, activo=True).exists():
            raise serializers.ValidationError('Tema no encontrado o inactivo.')
        return value


class SolicitarPreguntasIASerializer(serializers.Serializer):
    """Fase 4: solicitud para generar preguntas de quiz con IA."""
    tema_id = serializers.IntegerField()
    dificultad = serializers.ChoiceField(
        choices=['facil', 'media', 'dificil'], default='facil'
    )
    cantidad = serializers.IntegerField(min_value=1, max_value=10, default=5)

    def validate_tema_id(self, value):
        if not Tema.objects.filter(id=value, activo=True).exists():
            raise serializers.ValidationError('Tema no encontrado o inactivo.')
        return value


# ─── Pregunta / OpcionPregunta (CU-05) ───────────────────────────────────────

class OpcionPreguntaSerializer(serializers.ModelSerializer):
    class Meta:
        model = OpcionPregunta
        fields = ['id', 'texto', 'es_correcta']


class OpcionPreguntaFrontendSerializer(serializers.ModelSerializer):
    """Versión sin revelar la respuesta correcta (para el estudiante)."""
    class Meta:
        model = OpcionPregunta
        fields = ['id', 'texto']


class PreguntaSerializer(serializers.ModelSerializer):
    opciones = OpcionPreguntaSerializer(many=True)
    tema_nombre = serializers.ReadOnlyField(source='tema.nombre')
    subtema_nombre = serializers.ReadOnlyField(source='subtema.nombre')

    class Meta:
        model = Pregunta
        fields = [
            'id', 'enunciado', 'tema', 'tema_nombre', 'subtema', 'subtema_nombre',
            'nivel_dificultad', 'origen', 'explicacion', 'activo', 'opciones', 'fecha_creacion',
        ]
        read_only_fields = ['id', 'fecha_creacion', 'creado_por']

    def create(self, validated_data):
        opciones_data = validated_data.pop('opciones')
        pregunta = Pregunta.objects.create(**validated_data)
        for opcion_data in opciones_data:
            OpcionPregunta.objects.create(pregunta=pregunta, **opcion_data)
        return pregunta

    def update(self, instance, validated_data):
        opciones_data = validated_data.pop('opciones', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if opciones_data is not None:
            instance.opciones.all().delete()
            for opcion_data in opciones_data:
                OpcionPregunta.objects.create(pregunta=instance, **opcion_data)
        return instance

    def validate_opciones(self, value):
        if len(value) < 2:
            raise serializers.ValidationError('Debe haber al menos 2 opciones.')
        correctas = [o for o in value if o.get('es_correcta')]
        if len(correctas) != 1:
            raise serializers.ValidationError('Debe haber exactamente 1 opción correcta.')
        return value


class PreguntaFrontendSerializer(serializers.ModelSerializer):
    """Versión para el estudiante: sin revelar la respuesta correcta."""
    opciones = OpcionPreguntaFrontendSerializer(many=True, read_only=True)
    tema_nombre = serializers.ReadOnlyField(source='tema.nombre')

    class Meta:
        model = Pregunta
        fields = ['id', 'enunciado', 'tema_nombre', 'nivel_dificultad', 'opciones']


# ─── Quiz / ResultadoQuiz (CU-07) ────────────────────────────────────────────

class RespuestaQuizSerializer(serializers.Serializer):
    tema_id = serializers.IntegerField()
    respuestas = serializers.ListField(
        child=serializers.DictField(),
        help_text='[{pregunta_id: int, opcion_id: int}]',
    )

    def validate_tema_id(self, value):
        if not Tema.objects.filter(id=value, activo=True).exists():
            raise serializers.ValidationError('Tema no encontrado.')
        return value

    def validate_respuestas(self, value):
        if not value:
            raise serializers.ValidationError('Debes responder al menos una pregunta.')
        for item in value:
            if 'pregunta_id' not in item or 'opcion_id' not in item:
                raise serializers.ValidationError(
                    'Cada respuesta debe tener pregunta_id y opcion_id.'
                )
        return value


class ResultadoQuizSerializer(serializers.ModelSerializer):
    tema_nombre = serializers.ReadOnlyField(source='tema.nombre')
    puntaje_porcentaje = serializers.SerializerMethodField()

    class Meta:
        model = ResultadoQuiz
        fields = [
            'id', 'tema', 'tema_nombre', 'puntaje', 'puntaje_porcentaje',
            'total_preguntas', 'respuestas_correctas',
            'respuestas_json', 'fecha_realizacion',
        ]
        read_only_fields = fields

    def get_puntaje_porcentaje(self, obj):
        return f'{obj.puntaje:.0%}'
