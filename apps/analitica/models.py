from django.conf import settings
from django.db import models


# ─── CU-20: Experimento A/B ──────────────────────────────────────────────────

class ExperimentoAB(models.Model):

    ESTADO_ACTIVO = 'activo'
    ESTADO_FINALIZADO = 'finalizado'
    ESTADO_CHOICES = [
        (ESTADO_ACTIVO, 'Activo'),
        (ESTADO_FINALIZADO, 'Finalizado'),
    ]

    nombre = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default=ESTADO_ACTIVO)
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name='experimentos_creados', db_column='creado_por_id'
    )
    fecha_inicio = models.DateTimeField(auto_now_add=True)
    fecha_fin = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'experimento_ab'
        ordering = ['-fecha_inicio']
        verbose_name = 'Experimento A/B'
        verbose_name_plural = 'Experimentos A/B'

    def __str__(self):
        return f'{self.nombre} [{self.estado}]'


class AsignacionExperimento(models.Model):

    GRUPO_EXPERIMENTAL = 'experimental'
    GRUPO_CONTROL = 'control'
    GRUPO_CHOICES = [
        (GRUPO_EXPERIMENTAL, 'Experimental (recomendación VARK)'),
        (GRUPO_CONTROL, 'Control (sin personalización)'),
    ]

    experimento = models.ForeignKey(
        ExperimentoAB, on_delete=models.CASCADE,
        related_name='asignaciones', db_column='experimento_id'
    )
    estudiante = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='asignaciones_experimento', db_column='estudiante_id'
    )
    grupo = models.CharField(max_length=20, choices=GRUPO_CHOICES)
    fecha_asignacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'asignacion_experimento'
        unique_together = ('experimento', 'estudiante')
        verbose_name = 'Asignación Experimento'
        verbose_name_plural = 'Asignaciones Experimento'

    def __str__(self):
        return f'{self.estudiante} → {self.experimento} [{self.grupo}]'


# ─── CU-22: Notificaciones ───────────────────────────────────────────────────

class Notificacion(models.Model):

    TIPO_NUEVO_RECURSO = 'nuevo_recurso'
    TIPO_NUEVO_QUIZ = 'nuevo_quiz'
    TIPO_SISTEMA = 'sistema'
    TIPO_CHOICES = [
        (TIPO_NUEVO_RECURSO, 'Nuevo recurso disponible'),
        (TIPO_NUEVO_QUIZ, 'Nuevo quiz disponible'),
        (TIPO_SISTEMA, 'Mensaje del sistema'),
    ]

    destinatario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='notificaciones', db_column='destinatario_id'
    )
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    titulo = models.CharField(max_length=255)
    mensaje = models.TextField()
    # Referencia opcional al recurso que originó la notificación
    recurso = models.ForeignKey(
        'contenido.Recurso', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='notificaciones', db_column='recurso_id'
    )
    leida = models.BooleanField(default=False)
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'notificacion'
        ordering = ['-fecha']
        verbose_name = 'Notificación'
        verbose_name_plural = 'Notificaciones'

    def __str__(self):
        return f'{self.destinatario} — {self.titulo} [{"leída" if self.leida else "no leída"}]'

