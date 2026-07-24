from django.conf import settings
from django.db import models


# ─── CU-04: Jerarquía de temas y subtemas ────────────────────────────────────

class Tema(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True)
    orden = models.PositiveSmallIntegerField(default=0)
    activo = models.BooleanField(default=True)

    class Meta:
        db_table = 'tema'
        ordering = ['orden', 'nombre']
        verbose_name = 'Tema'
        verbose_name_plural = 'Temas'

    def __str__(self):
        return self.nombre


class Subtema(models.Model):
    tema = models.ForeignKey(
        Tema, on_delete=models.CASCADE, related_name='subtemas', db_column='tema_id'
    )
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    orden = models.PositiveSmallIntegerField(default=0)
    activo = models.BooleanField(default=True)

    class Meta:
        db_table = 'subtema'
        ordering = ['tema', 'orden', 'nombre']
        unique_together = ('tema', 'nombre')
        verbose_name = 'Subtema'
        verbose_name_plural = 'Subtemas'

    def __str__(self):
        return f'{self.tema.nombre} › {self.nombre}'


# ─── CU-08: Repositorio de recursos académicos ───────────────────────────────

class Recurso(models.Model):

    VARK_VISUAL = 'V'
    VARK_AUDITIVO = 'A'
    VARK_LECTURA = 'R'
    VARK_KINESTESICO = 'K'
    VARK_CHOICES = [
        (VARK_VISUAL, 'Visual'),
        (VARK_AUDITIVO, 'Auditivo'),
        (VARK_LECTURA, 'Lectura/Escritura'),
        (VARK_KINESTESICO, 'Kinestésico'),
    ]

    NIVEL_BASICO = 'basico'
    NIVEL_INTERMEDIO = 'intermedio'
    NIVEL_AVANZADO = 'avanzado'
    NIVEL_CHOICES = [
        (NIVEL_BASICO, 'Básico'),
        (NIVEL_INTERMEDIO, 'Intermedio'),
        (NIVEL_AVANZADO, 'Avanzado'),
    ]

    TIPO_VIDEO = 'video'
    TIPO_ARTICULO = 'articulo'
    TIPO_EJERCICIO = 'ejercicio'
    TIPO_DOCUMENTO = 'documento'
    TIPO_CHOICES = [
        (TIPO_VIDEO, 'Video'),
        (TIPO_ARTICULO, 'Artículo'),
        (TIPO_EJERCICIO, 'Ejercicio'),
        (TIPO_DOCUMENTO, 'Documento'),
    ]

    titulo = models.CharField(max_length=255)
    url = models.URLField(max_length=500)
    descripcion = models.TextField(blank=True)
    tema = models.ForeignKey(
        Tema, on_delete=models.PROTECT, related_name='recursos', db_column='tema_id'
    )
    subtema = models.ForeignKey(
        Subtema, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='recursos', db_column='subtema_id'
    )
    categoria_vark = models.CharField(max_length=1, choices=VARK_CHOICES, db_index=True)
    nivel_complejidad = models.CharField(max_length=20, choices=NIVEL_CHOICES, db_index=True)
    tipo_formato = models.CharField(max_length=20, choices=TIPO_CHOICES, default=TIPO_ARTICULO)
    activo = models.BooleanField(default=True)
    url_valida = models.BooleanField(default=True)
    ultima_verificacion = models.DateTimeField(null=True, blank=True)

    # Trazabilidad
    sugerido_por_ia = models.BooleanField(default=False)
    validado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='recursos_validados', db_column='validado_por_id'
    )
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name='recursos_creados', db_column='creado_por_id'
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'recurso'
        ordering = ['-fecha_creacion']
        verbose_name = 'Recurso'
        verbose_name_plural = 'Recursos'

    def __str__(self):
        return f'[{self.categoria_vark}] {self.titulo}'


# ─── CU-09 / CU-10: Sugerencias de IA ───────────────────────────────────────

class SugerenciaIA(models.Model):

    ESTADO_PENDIENTE = 'pendiente'
    ESTADO_APROBADO = 'aprobado'
    ESTADO_RECHAZADO = 'rechazado'
    ESTADO_CHOICES = [
        (ESTADO_PENDIENTE, 'Pendiente'),
        (ESTADO_APROBADO, 'Aprobado'),
        (ESTADO_RECHAZADO, 'Rechazado'),
    ]

    titulo = models.CharField(max_length=255)
    url = models.URLField(max_length=500)
    descripcion = models.TextField(blank=True)
    justificacion_pedagogica = models.TextField()
    tema = models.ForeignKey(
        Tema, on_delete=models.CASCADE, related_name='sugerencias_ia', db_column='tema_id'
    )
    categoria_vark = models.CharField(max_length=1, choices=Recurso.VARK_CHOICES)
    nivel_complejidad = models.CharField(
        max_length=20, choices=Recurso.NIVEL_CHOICES, default=Recurso.NIVEL_BASICO
    )
    tipo_formato = models.CharField(
        max_length=20, choices=Recurso.TIPO_CHOICES, default=Recurso.TIPO_ARTICULO
    )
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default=ESTADO_PENDIENTE)
    revisado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='sugerencias_revisadas', db_column='revisado_por_id'
    )
    recurso_creado = models.OneToOneField(
        Recurso, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='sugerencia_origen'
    )
    fecha_sugerencia = models.DateTimeField(auto_now_add=True)
    fecha_revision = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'sugerencia_ia'
        ordering = ['-fecha_sugerencia']
        verbose_name = 'Sugerencia IA'
        verbose_name_plural = 'Sugerencias IA'

    def __str__(self):
        return f'[{self.estado}] {self.titulo}'


# ─── CU-05: Banco de preguntas para quizzes ──────────────────────────────────

class Pregunta(models.Model):

    DIFICULTAD_FACIL = 'facil'
    DIFICULTAD_MEDIA = 'media'
    DIFICULTAD_DIFICIL = 'dificil'
    DIFICULTAD_CHOICES = [
        (DIFICULTAD_FACIL, 'Fácil'),
        (DIFICULTAD_MEDIA, 'Media'),
        (DIFICULTAD_DIFICIL, 'Difícil'),
    ]

    ORIGEN_MANUAL = 'manual'
    ORIGEN_IA = 'ia'
    ORIGEN_CHOICES = [
        (ORIGEN_MANUAL, 'Manual'),
        (ORIGEN_IA, 'Generada por IA'),
    ]

    enunciado = models.TextField()
    tema = models.ForeignKey(
        Tema, on_delete=models.CASCADE, related_name='preguntas', db_column='tema_id'
    )
    subtema = models.ForeignKey(
        Subtema, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='preguntas', db_column='subtema_id'
    )
    nivel_dificultad = models.CharField(
        max_length=10, choices=DIFICULTAD_CHOICES, default=DIFICULTAD_FACIL
    )
    # Fase 4: trazabilidad de IA y retroalimentación (RP06)
    origen = models.CharField(max_length=10, choices=ORIGEN_CHOICES, default=ORIGEN_MANUAL)
    explicacion = models.TextField(blank=True, default='')
    activo = models.BooleanField(default=True)
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name='preguntas_creadas', db_column='creado_por_id'
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'pregunta'
        verbose_name = 'Pregunta'
        verbose_name_plural = 'Preguntas'

    def __str__(self):
        return f'[{self.tema}] {self.enunciado[:60]}...'


class OpcionPregunta(models.Model):
    pregunta = models.ForeignKey(
        Pregunta, on_delete=models.CASCADE,
        related_name='opciones', db_column='pregunta_id'
    )
    texto = models.CharField(max_length=500)
    es_correcta = models.BooleanField(default=False)

    class Meta:
        db_table = 'opcion_pregunta'
        verbose_name = 'Opción de Pregunta'
        verbose_name_plural = 'Opciones de Pregunta'

    def __str__(self):
        marca = '✓' if self.es_correcta else '✗'
        return f'{marca} {self.texto[:60]}'


# ─── CU-07: Resultados de quizzes ────────────────────────────────────────────

class ResultadoQuiz(models.Model):

    estudiante = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='resultados_quiz', db_column='estudiante_id'
    )
    tema = models.ForeignKey(
        Tema, on_delete=models.CASCADE, related_name='resultados_quiz', db_column='tema_id'
    )
    puntaje = models.FloatField()
    total_preguntas = models.PositiveSmallIntegerField()
    respuestas_correctas = models.PositiveSmallIntegerField()
    respuestas_json = models.JSONField(
        help_text='[{pregunta_id, opcion_elegida_id, es_correcta}]'
    )
    fecha_realizacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'resultado_quiz'
        ordering = ['-fecha_realizacion']
        verbose_name = 'Resultado Quiz'
        verbose_name_plural = 'Resultados Quiz'

    def __str__(self):
        return f'{self.estudiante} — {self.tema} — {self.puntaje:.0%}'
