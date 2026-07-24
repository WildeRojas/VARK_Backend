from django.conf import settings
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import (
    ConfiguracionTestVARK,
    OpcionVARK,
    PerfilVARK,
    PreguntaVARK,
    Usuario,
)


class RegistroSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = Usuario
        fields = ['email', 'nombre', 'apellido', 'rol', 'password']

    def validate_email(self, value):
        value = value.lower().strip()
        dominio = getattr(settings, 'DOMINIO_INSTITUCIONAL', '')
        if dominio and not value.endswith(f'@{dominio}'):
            raise serializers.ValidationError(
                f'El correo debe pertenecer al dominio @{dominio}.'
            )
        return value

    def validate_rol(self, value):
        roles_validos = [r[0] for r in Usuario.ROL_CHOICES]
        if value not in roles_validos:
            raise serializers.ValidationError(
                f'Rol no válido. Opciones permitidas: {roles_validos}.'
            )
        return value

    def create(self, validated_data):
        password = validated_data.pop('password')
        usuario = Usuario(**validated_data)
        usuario.set_password(password)
        usuario.save()
        PerfilVARK.objects.create(usuario=usuario)
        return usuario


class UsuarioSerializer(serializers.ModelSerializer):
    nombre_completo = serializers.ReadOnlyField()

    class Meta:
        model = Usuario
        fields = [
            'id', 'email', 'nombre', 'apellido', 'nombre_completo', 'rol',
            'foto', 'carrera', 'semestre', 'fecha_registro',
        ]
        read_only_fields = ['id', 'rol', 'fecha_registro']


class MeUpdateSerializer(serializers.ModelSerializer):
    """Edición del propio perfil (Fase 7). No permite cambiar el rol."""
    class Meta:
        model = Usuario
        fields = ['nombre', 'apellido', 'email', 'foto', 'carrera', 'semestre']

    def validate_email(self, value):
        value = value.lower().strip()
        qs = Usuario.objects.filter(email=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError('Ya existe un usuario con ese correo.')
        return value


class CambiarPasswordSerializer(serializers.Serializer):
    password_actual = serializers.CharField()
    password_nueva = serializers.CharField(min_length=8)


class UsuarioAdminSerializer(serializers.ModelSerializer):
    """Gestión de usuarios por el Administrador (CRUD). Fase 2."""
    nombre_completo = serializers.ReadOnlyField()
    password = serializers.CharField(write_only=True, required=False, min_length=8)

    class Meta:
        model = Usuario
        fields = [
            'id', 'email', 'nombre', 'apellido', 'nombre_completo',
            'rol', 'is_active', 'fecha_registro', 'password',
        ]
        read_only_fields = ['id', 'fecha_registro']

    def create(self, validated_data):
        password = validated_data.pop('password', None) or 'cambiar123'
        usuario = Usuario(**validated_data)
        usuario.set_password(password)
        usuario.save()
        if usuario.rol == Usuario.ROL_ESTUDIANTE:
            PerfilVARK.objects.get_or_create(usuario=usuario)
        return usuario

    def update(self, instance, validated_data):
        # El cambio de contraseña tiene su propio endpoint; aquí se ignora.
        validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class PerfilVARKSerializer(serializers.ModelSerializer):
    vector = serializers.SerializerMethodField()
    estilo_dominante = serializers.SerializerMethodField()

    class Meta:
        model = PerfilVARK
        fields = [
            'puntaje_visual', 'puntaje_auditivo', 'puntaje_lectura',
            'puntaje_kinestesico', 'test_completado', 'fecha_test',
            'vector', 'estilo_dominante',
        ]

    def get_vector(self, obj):
        return obj.vector

    def get_estilo_dominante(self, obj):
        vector = obj.vector
        return max(vector, key=vector.get)


class LoginSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        data['usuario'] = UsuarioSerializer(self.user).data
        try:
            data['vark_completado'] = self.user.perfil_vark.test_completado
        except PerfilVARK.DoesNotExist:
            data['vark_completado'] = False
        return data


# ─── Fase 3: Banco y configuración del test VARK (admin) ──────────────────────

class OpcionVARKSerializer(serializers.ModelSerializer):
    class Meta:
        model = OpcionVARK
        fields = ['id', 'texto', 'estilo', 'peso', 'orden']
        extra_kwargs = {'id': {'read_only': True}}

    def validate_estilo(self, value):
        if value not in {'V', 'A', 'R', 'K'}:
            raise serializers.ValidationError('El estilo debe ser V, A, R o K.')
        return value


class PreguntaVARKSerializer(serializers.ModelSerializer):
    opciones = OpcionVARKSerializer(many=True)

    class Meta:
        model = PreguntaVARK
        fields = [
            'id', 'enunciado', 'contexto', 'activo', 'origen',
            'opciones', 'creado_en',
        ]
        read_only_fields = ['id', 'creado_en']

    def validate_opciones(self, value):
        if len(value) != 4:
            raise serializers.ValidationError('Cada pregunta debe tener exactamente 4 opciones.')
        estilos = {o['estilo'] for o in value}
        if estilos != {'V', 'A', 'R', 'K'}:
            raise serializers.ValidationError(
                'Las 4 opciones deben cubrir los estilos V, A, R y K (uno cada uno).'
            )
        return value

    def create(self, validated_data):
        opciones = validated_data.pop('opciones')
        admin = self.context['request'].user if 'request' in self.context else None
        pregunta = PreguntaVARK.objects.create(aprobada_por=admin, **validated_data)
        for i, op in enumerate(opciones):
            OpcionVARK.objects.create(pregunta=pregunta, orden=op.get('orden', i), **{
                k: v for k, v in op.items() if k != 'orden'
            })
        return pregunta

    def update(self, instance, validated_data):
        opciones = validated_data.pop('opciones', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if opciones is not None:
            instance.opciones.all().delete()
            for i, op in enumerate(opciones):
                OpcionVARK.objects.create(pregunta=instance, orden=op.get('orden', i), **{
                    k: v for k, v in op.items() if k != 'orden'
                })
        return instance


class ConfiguracionTestVARKSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConfiguracionTestVARK
        fields = ['modo', 'num_preguntas', 'contexto_tematico', 'usar_fallback', 'actualizado_en']
        read_only_fields = ['actualizado_en']

    def validate_num_preguntas(self, value):
        if not (12 <= value <= 20):
            raise serializers.ValidationError('El número de preguntas debe estar entre 12 y 20.')
        return value


class RespuestasTestSerializer(serializers.Serializer):
    sesion_id = serializers.IntegerField()
    respuestas = serializers.DictField(
        child=serializers.CharField(max_length=1),
        help_text='Diccionario {pregunta_id: opcion_id}, ej: {"1": "a", "2": "c"}',
    )

    def validate_respuestas(self, value):
        if not value:
            raise serializers.ValidationError('Las respuestas no pueden estar vacías.')
        return value
