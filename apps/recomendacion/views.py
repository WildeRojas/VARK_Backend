from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import EsAdmin, EsDocenteOAdmin, EsEstudiante

from .models import (
    ConfiguracionMotor,
    EventoClickstream,
    HistorialPerfilVARK,
    Recomendacion,
    ValoracionRecurso,
)
from .serializers import (
    ConfiguracionMotorSerializer,
    EventoClickstreamSerializer,
    HistorialPerfilVARKSerializer,
    RecomendacionSerializer,
    SolicitarRecomendacionSerializer,
    ValoracionRecursoSerializer,
)


# ─── CU-12 / CU-13: Recomendaciones ─────────────────────────────────────────

class RecomendarRecursosView(APIView):
    """
    POST /api/recomendacion/recomendar/
    Genera recomendaciones CBF para el estudiante autenticado en un tema dado.
    Guarda las recomendaciones y retorna la lista con justificaciones.
    """
    permission_classes = [EsEstudiante]

    def post(self, request):
        serializer = SolicitarRecomendacionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        tema_id = serializer.validated_data['tema_id']
        usar_groq = serializer.validated_data.get('usar_groq', False)

        from apps.contenido.models import Tema
        from .services.cbf_service import (
            generar_justificacion_groq,
            grupo_experimento_activo,
            recomendar_recursos,
            recomendar_sin_personalizacion,
        )

        # Fase 6 (A/B): el grupo del experimento cambia la experiencia.
        grupo = grupo_experimento_activo(request.user)
        if grupo == 'control':
            resultados = recomendar_sin_personalizacion(tema_id)
            personalizado = False
        else:
            # 'experimental' o sin experimento → motor personalizado normal
            resultados = recomendar_recursos(request.user, tema_id)
            personalizado = True

        if not resultados:
            detalle = (
                'No hay recursos disponibles que coincidan con tu perfil VARK.'
                if personalizado else
                'No hay recursos disponibles para este tema en este momento.'
            )
            return Response({'detail': detalle}, status=status.HTTP_200_OK)

        tema = Tema.objects.get(pk=tema_id)
        try:
            vector_snapshot = request.user.perfil_vark.vector
        except Exception:
            vector_snapshot = {'V': 0, 'A': 0, 'R': 0, 'K': 0}

        recomendaciones_guardadas = []
        for item in resultados:
            recurso = item['recurso']
            justificacion = item['justificacion']

            # La justificación con IA solo aplica al grupo personalizado
            if usar_groq and personalizado:
                texto_groq = generar_justificacion_groq(recurso, vector_snapshot, tema.nombre)
                if texto_groq:
                    justificacion = texto_groq

            rec = Recomendacion.objects.create(
                estudiante=request.user,
                recurso=recurso,
                tema=tema,
                puntuacion=item['puntuacion'],
                justificacion=justificacion,
                vector_vark_snapshot=vector_snapshot,
                grupo_experimento=grupo or '',
            )
            recomendaciones_guardadas.append(rec)

        return Response(
            RecomendacionSerializer(recomendaciones_guardadas, many=True).data,
            status=status.HTTP_201_CREATED,
        )


class RecomendacionHistorialView(APIView):
    """
    GET /api/recomendacion/mis-recomendaciones/
    Retorna el historial de recomendaciones del estudiante autenticado.
    """
    permission_classes = [EsEstudiante]

    def get(self, request):
        recomendaciones = (
            Recomendacion.objects
            .filter(estudiante=request.user)
            .select_related('recurso', 'tema')
            .order_by('-fecha_recomendacion')
        )
        return Response(RecomendacionSerializer(recomendaciones, many=True).data)


class MarcarRecomendacionVistaView(APIView):
    """
    PATCH /api/recomendacion/<pk>/vista/
    Marca una recomendación como vista por el estudiante.
    """
    permission_classes = [EsEstudiante]

    def patch(self, request, pk):
        try:
            rec = Recomendacion.objects.get(pk=pk, estudiante=request.user)
        except Recomendacion.DoesNotExist:
            return Response({'detail': 'Recomendación no encontrada.'}, status=status.HTTP_404_NOT_FOUND)
        rec.vista = True
        rec.save(update_fields=['vista'])
        return Response({'detail': 'Marcada como vista.'})


# ─── CU-15: Clickstream ───────────────────────────────────────────────────────

class RegistrarEventoClickstreamView(APIView):
    """
    POST /api/recomendacion/clickstream/
    Registra un evento de interacción del estudiante con un recurso.
    """
    permission_classes = [EsEstudiante]

    def post(self, request):
        serializer = EventoClickstreamSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save(estudiante=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


# ─── CU-14: Valoraciones ─────────────────────────────────────────────────────

class ValoracionRecursoView(APIView):
    """
    POST   /api/recomendacion/valoraciones/   → crear o actualizar valoración
    GET    /api/recomendacion/valoraciones/   → listar valoraciones del estudiante
    """
    permission_classes = [EsEstudiante]

    def get(self, request):
        valoraciones = ValoracionRecurso.objects.filter(
            estudiante=request.user
        ).select_related('recurso')
        return Response(ValoracionRecursoSerializer(valoraciones, many=True).data)

    def post(self, request):
        recurso_id = request.data.get('recurso')
        if not recurso_id:
            return Response({'recurso': 'Este campo es requerido.'}, status=status.HTTP_400_BAD_REQUEST)

        # Upsert: crear o actualizar
        valoracion, created = ValoracionRecurso.objects.update_or_create(
            estudiante=request.user,
            recurso_id=recurso_id,
            defaults={
                'valoracion': request.data.get('valoracion', 'util'),
                'comentario': request.data.get('comentario', ''),
            },
        )
        serializer = ValoracionRecursoSerializer(valoracion)
        status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
        return Response(serializer.data, status=status_code)


# ─── CU-16: Historial evolución del perfil VARK ──────────────────────────────

class HistorialPerfilVARKView(APIView):
    """
    GET /api/recomendacion/perfil/historial/
    Historial de cambios del vector VARK del estudiante autenticado.
    """
    permission_classes = [EsEstudiante]

    def get(self, request):
        historial = HistorialPerfilVARK.objects.filter(
            estudiante=request.user
        ).order_by('-fecha')
        return Response(HistorialPerfilVARKSerializer(historial, many=True).data)


# ─── CU-06: Configuración del motor ──────────────────────────────────────────

class ConfiguracionMotorView(APIView):
    """
    GET  /api/recomendacion/configuracion/   → ver configuración actual
    PUT  /api/recomendacion/configuracion/   → actualizar (solo Admin)
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        config = ConfiguracionMotor.obtener()
        return Response(ConfiguracionMotorSerializer(config).data)

    def put(self, request):
        if request.user.rol != 'administrador':
            return Response(status=status.HTTP_403_FORBIDDEN)
        config = ConfiguracionMotor.obtener()
        serializer = ConfiguracionMotorSerializer(config, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ─── Fase 5: Estado y métricas del modelo de ML ──────────────────────────────

class MLEstadoView(APIView):
    """
    GET /api/recomendacion/ml/estado/
    Devuelve si hay modelo entrenado, sus métricas y la mezcla CBF/ML configurada.
    """
    permission_classes = [EsDocenteOAdmin]

    def get(self, request):
        try:
            from apps.recomendacion.services.ml import inference as ml_inf
            disponible = ml_inf.modelo_disponible()
            metricas = ml_inf.cargar_metricas()
        except Exception:
            disponible, metricas = False, None

        config = ConfiguracionMotor.obtener()
        return Response({
            'modelo_disponible': disponible,
            'usar_ml': config.usar_ml,
            'peso_cbf': config.peso_cbf,
            'peso_ml': config.peso_ml,
            'metricas': metricas,
        })

