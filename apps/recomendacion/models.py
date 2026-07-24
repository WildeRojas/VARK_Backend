from django.conf import settings
from django.db import models


# ─── CU-15: Clickstream — eventos de interacción ─────────────────────────────

class EventoClickstream(models.Model):

    TIPO_CLIC = 'clic'
    TIPO_PERMANENCIA = 'permanencia'
    TIPO_RETORNO = 'retorno'
    TIPO_CIERRE = 'cierre'
    TIPO_CHOICES = [
        (TIPO_CLIC, 'Clic en recurso'),
        (TIPO_PERMANENCIA, 'Permanencia en URL'),
        (TIPO_RETORNO, 'Retorno a recurso'),
        (TIPO_CIERRE, 'Cierre de recurso'),
    ]

    estudiante = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='eventos_clickstream', db_column='estudiante_id'
    )
    recurso = models.ForeignKey(
        'contenido.Recurso', on_delete=models.CASCADE,
        related_name='eventos_clickstream', db_column='recurso_id'
    )
    tipo_evento = models.CharField(max_length=20, choices=TIPO_CHOICES)
    # Para eventos de permanencia: segundos de permanencia
    duracion_segundos = models.PositiveIntegerField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    procesado = models.BooleanField(default=False, db_index=True)

    class Meta:
        db_table = 'evento_clickstream'
        ordering = ['-timestamp']
        verbose_name = 'Evento Clickstream'
        verbose_name_plural = 'Eventos Clickstream'

    def __str__(self):
        return f'{self.estudiante} — {self.tipo_evento} — {self.recurso}'


# ─── CU-14: Valoraciones de recursos ─────────────────────────────────────────

class ValoracionRecurso(models.Model):

    UTIL = 'util'
    NO_UTIL = 'no_util'
    VALORACION_CHOICES = [
        (UTIL, 'Útil'),
        (NO_UTIL, 'No útil'),
    ]

    estudiante = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='valoraciones', db_column='estudiante_id'
    )
    recurso = models.ForeignKey(
        'contenido.Recurso', on_delete=models.CASCADE,
        related_name='valoraciones', db_column='recurso_id'
    )
    valoracion = models.CharField(max_length=10, choices=VALORACION_CHOICES)
    comentario = models.TextField(blank=True)
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'valoracion_recurso'
        unique_together = ('estudiante', 'recurso')
        verbose_name = 'Valoración de Recurso'
        verbose_name_plural = 'Valoraciones de Recursos'

    def __str__(self):
        return f'{self.estudiante} — {self.recurso} — {self.valoracion}'


# ─── CU-12 / CU-13: Recomendaciones generadas ────────────────────────────────

class Recomendacion(models.Model):

    estudiante = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='recomendaciones', db_column='estudiante_id'
    )
    recurso = models.ForeignKey(
        'contenido.Recurso', on_delete=models.CASCADE,
        related_name='recomendaciones', db_column='recurso_id'
    )
    tema = models.ForeignKey(
        'contenido.Tema', on_delete=models.CASCADE,
        related_name='recomendaciones', db_column='tema_id'
    )
    # Puntuación de similitud calculada por el motor CBF (0.0 – 1.0)
    puntuacion = models.FloatField()
    # CU-13: justificación en lenguaje natural
    justificacion = models.TextField()
    # Snapshot del vector VARK en el momento de la recomendación
    vector_vark_snapshot = models.JSONField()
    # Fase 6 (A/B): grupo del experimento al que pertenecía esta recomendación
    # ('experimental', 'control' o '' si el estudiante no estaba en un experimento)
    grupo_experimento = models.CharField(max_length=20, blank=True, default='')
    fecha_recomendacion = models.DateTimeField(auto_now_add=True)
    vista = models.BooleanField(default=False)

    class Meta:
        db_table = 'recomendacion'
        ordering = ['-fecha_recomendacion', '-puntuacion']
        verbose_name = 'Recomendación'
        verbose_name_plural = 'Recomendaciones'

    def __str__(self):
        return f'{self.estudiante} → {self.recurso} ({self.puntuacion:.2f})'


# ─── CU-16: Historial de evolución del perfil VARK ───────────────────────────

class HistorialPerfilVARK(models.Model):

    ORIGEN_CLICKSTREAM = 'clickstream'
    ORIGEN_QUIZ = 'quiz'
    ORIGEN_TEST_INICIAL = 'test_inicial'
    ORIGEN_CHOICES = [
        (ORIGEN_CLICKSTREAM, 'Procesamiento Clickstream'),
        (ORIGEN_QUIZ, 'Resultado de Quiz'),
        (ORIGEN_TEST_INICIAL, 'Test VARK Inicial'),
    ]

    estudiante = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='historial_perfil_vark', db_column='estudiante_id'
    )
    vector_anterior = models.JSONField()
    vector_nuevo = models.JSONField()
    origen = models.CharField(max_length=20, choices=ORIGEN_CHOICES)
    fecha = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = 'historial_perfil_vark'
        ordering = ['-fecha']
        verbose_name = 'Historial Perfil VARK'
        verbose_name_plural = 'Historial Perfil VARK'

    def __str__(self):
        return f'{self.estudiante} — {self.origen} — {self.fecha.date()}'


# ─── CU-06: Parámetros del motor de recomendación ────────────────────────────

class ConfiguracionMotor(models.Model):
    """Singleton de configuración del motor. Solo debe existir un registro."""

    factor_decaimiento = models.FloatField(
        default=0.85,
        help_text='Factor λ del decaimiento temporal (0 < λ ≤ 1). '
                  'Multiplica el peso de eventos cada día de antigüedad.',
    )
    umbral_similitud = models.FloatField(
        default=0.3,
        help_text='Puntuación mínima (0–1) para incluir un recurso en la recomendación.',
    )
    max_recomendaciones = models.PositiveSmallIntegerField(
        default=8,
        help_text='Número máximo de recursos a recomendar por sesión.',
    )
    peso_valoracion_util = models.FloatField(
        default=0.2,
        help_text='Peso adicional para recursos con valoración "útil" del estudiante.',
    )
    dias_ventana_clickstream = models.PositiveSmallIntegerField(
        default=30,
        help_text='Días hacia atrás a considerar para el procesamiento de Clickstream.',
    )
    # Fase 5 (ML): mezcla del score final = peso_cbf·similitud + peso_ml·prob_utilidad_ML
    peso_cbf = models.FloatField(
        default=0.6,
        help_text='Peso de la similitud coseno (CBF) en el score final (0–1).',
    )
    peso_ml = models.FloatField(
        default=0.4,
        help_text='Peso de la probabilidad de utilidad del modelo ML en el score final (0–1).',
    )
    usar_ml = models.BooleanField(
        default=True,
        help_text='Si está activo y hay modelo entrenado, combina ML con CBF. Si no, solo CBF.',
    )
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'configuracion_motor'
        verbose_name = 'Configuración del Motor'
        verbose_name_plural = 'Configuración del Motor'

    def save(self, *args, **kwargs):
        self.pk = 1  # Forzar singleton
        super().save(*args, **kwargs)

    @classmethod
    def obtener(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def __str__(self):
        return f'Configuración del Motor (λ={self.factor_decaimiento})'
