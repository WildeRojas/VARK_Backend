from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone

from .managers import UsuarioManager


class Usuario(AbstractBaseUser, PermissionsMixin):

    ROL_ESTUDIANTE = 'estudiante'
    ROL_DOCENTE = 'docente'
    ROL_ADMINISTRADOR = 'administrador'

    ROL_CHOICES = [
        (ROL_ESTUDIANTE, 'Estudiante'),
        (ROL_DOCENTE, 'Docente'),
        (ROL_ADMINISTRADOR, 'Administrador'),
    ]

    email = models.EmailField(unique=True, db_index=True)
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    rol = models.CharField(max_length=20, choices=ROL_CHOICES, default=ROL_ESTUDIANTE)
    # Perfil (Fase 7): foto por URL y datos académicos opcionales
    foto = models.URLField(blank=True, default='')
    carrera = models.CharField(max_length=120, blank=True, default='')
    semestre = models.CharField(max_length=20, blank=True, default='')
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    fecha_registro = models.DateTimeField(default=timezone.now)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['nombre', 'apellido']

    objects = UsuarioManager()

    class Meta:
        db_table = 'usuario'
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'

    def __str__(self):
        return f'{self.nombre} {self.apellido} <{self.email}>'

    @property
    def nombre_completo(self):
        return f'{self.nombre} {self.apellido}'


class PerfilVARK(models.Model):

    usuario = models.OneToOneField(
        Usuario,
        on_delete=models.CASCADE,
        related_name='perfil_vark',
        db_column='usuario_id',
    )
    puntaje_visual = models.FloatField(default=0.0)
    puntaje_auditivo = models.FloatField(default=0.0)
    puntaje_lectura = models.FloatField(default=0.0)
    puntaje_kinestesico = models.FloatField(default=0.0)
    test_completado = models.BooleanField(default=False)
    fecha_test = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'perfil_vark'
        verbose_name = 'Perfil VARK'
        verbose_name_plural = 'Perfiles VARK'

    def __str__(self):
        return f'Perfil VARK — {self.usuario}'

    @property
    def vector(self):
        return {
            'V': self.puntaje_visual,
            'A': self.puntaje_auditivo,
            'R': self.puntaje_lectura,
            'K': self.puntaje_kinestesico,
        }


class SesionTestVARK(models.Model):

    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name='sesiones_test_vark',
        db_column='usuario_id',
    )
    preguntas_json = models.JSONField()
    completado = models.BooleanField(default=False)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'sesion_test_vark'
        verbose_name = 'Sesión Test VARK'
        verbose_name_plural = 'Sesiones Test VARK'

    def __str__(self):
        estado = 'completado' if self.completado else 'pendiente'
        return f'Test de {self.usuario} — {estado}'


# ─── Fase 3: Banco y configuración del test VARK (editable por el admin) ───────

class PreguntaVARK(models.Model):
    """Pregunta del banco oficial del test VARK, gestionada por el administrador."""

    ORIGEN_IA = 'ia'
    ORIGEN_MANUAL = 'manual'
    ORIGEN_CHOICES = [
        (ORIGEN_IA, 'Generada por IA'),
        (ORIGEN_MANUAL, 'Manual'),
    ]

    enunciado = models.TextField()
    contexto = models.CharField(max_length=200, blank=True, default='')
    activo = models.BooleanField(default=True)
    origen = models.CharField(max_length=10, choices=ORIGEN_CHOICES, default=ORIGEN_MANUAL)
    aprobada_por = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='preguntas_vark_aprobadas',
    )
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'pregunta_vark'
        verbose_name = 'Pregunta VARK'
        verbose_name_plural = 'Preguntas VARK'
        ordering = ['-creado_en']

    def __str__(self):
        return self.enunciado[:60]


class OpcionVARK(models.Model):
    """Opción de una PreguntaVARK, con su estilo VARK asociado (oculto al estudiante)."""

    ESTILO_CHOICES = [
        ('V', 'Visual'),
        ('A', 'Auditivo'),
        ('R', 'Lectura/Escritura'),
        ('K', 'Kinestésico'),
    ]

    pregunta = models.ForeignKey(
        PreguntaVARK,
        on_delete=models.CASCADE,
        related_name='opciones',
    )
    texto = models.TextField()
    estilo = models.CharField(max_length=1, choices=ESTILO_CHOICES)
    peso = models.FloatField(default=1.0)
    orden = models.PositiveSmallIntegerField(default=0)

    class Meta:
        db_table = 'opcion_vark'
        verbose_name = 'Opción VARK'
        verbose_name_plural = 'Opciones VARK'
        ordering = ['orden', 'id']

    def __str__(self):
        return f'[{self.estilo}] {self.texto[:40]}'


class ConfiguracionTestVARK(models.Model):
    """Configuración singleton del test VARK (la edita el administrador)."""

    MODO_DINAMICO = 'dinamico_ia'
    MODO_BANCO = 'banco_fijo'
    MODO_CHOICES = [
        (MODO_DINAMICO, 'Generación dinámica con IA'),
        (MODO_BANCO, 'Banco fijo de preguntas'),
    ]

    modo = models.CharField(max_length=20, choices=MODO_CHOICES, default=MODO_DINAMICO)
    num_preguntas = models.PositiveSmallIntegerField(default=15)
    contexto_tematico = models.CharField(
        max_length=200,
        default='aprender conceptos de programación (algoritmos, estructuras de datos, POO)',
    )
    usar_fallback = models.BooleanField(default=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'configuracion_test_vark'
        verbose_name = 'Configuración Test VARK'
        verbose_name_plural = 'Configuración Test VARK'

    def __str__(self):
        return f'Config Test VARK ({self.get_modo_display()})'

    def save(self, *args, **kwargs):
        # Forzar singleton: siempre pk=1
        self.pk = 1
        # Mantener num_preguntas en el rango acordado [12, 20]
        self.num_preguntas = max(12, min(20, self.num_preguntas))
        super().save(*args, **kwargs)

    @classmethod
    def get_solo(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj
