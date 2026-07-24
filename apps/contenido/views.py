import random

from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import (
    EsDocenteOAdmin,
    EsDocenteOAdminOLecturaEstudiante,
    EsEstudiante,
)

from .models import (
    OpcionPregunta,
    Pregunta,
    Recurso,
    ResultadoQuiz,
    Subtema,
    SugerenciaIA,
    Tema,
)
from .serializers import (
    PreguntaFrontendSerializer,
    PreguntaSerializer,
    RecursoSerializer,
    RespuestaQuizSerializer,
    ResultadoQuizSerializer,
    SolicitarPreguntasIASerializer,
    SolicitarSugerenciaIASerializer,
    SugerenciaIASerializer,
    SubtemaSerializer,
    TemaSerializer,
    TemaSimpleSerializer,
)

PREGUNTAS_POR_QUIZ = 10


# ─── CU-04: Temas ────────────────────────────────────────────────────────────

class TemaListCreateView(APIView):
    permission_classes = [EsDocenteOAdminOLecturaEstudiante]

    def get(self, request):
        temas = Tema.objects.filter(activo=True)
        serializer = TemaSerializer(temas, many=True)
        return Response(serializer.data)

    def post(self, request):
        if request.user.rol not in ('docente', 'administrador'):
            return Response(status=status.HTTP_403_FORBIDDEN)
        serializer = TemaSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TemaDetailView(APIView):
    permission_classes = [EsDocenteOAdminOLecturaEstudiante]

    def _get_tema(self, pk):
        try:
            return Tema.objects.get(pk=pk)
        except Tema.DoesNotExist:
            return None

    def get(self, request, pk):
        tema = self._get_tema(pk)
        if not tema:
            return Response({'detail': 'Tema no encontrado.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(TemaSerializer(tema).data)

    def put(self, request, pk):
        if request.user.rol not in ('docente', 'administrador'):
            return Response(status=status.HTTP_403_FORBIDDEN)
        tema = self._get_tema(pk)
        if not tema:
            return Response({'detail': 'Tema no encontrado.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = TemaSerializer(tema, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        if request.user.rol not in ('docente', 'administrador'):
            return Response(status=status.HTTP_403_FORBIDDEN)
        tema = self._get_tema(pk)
        if not tema:
            return Response({'detail': 'Tema no encontrado.'}, status=status.HTTP_404_NOT_FOUND)
        tema.activo = False
        tema.save(update_fields=['activo'])
        return Response(status=status.HTTP_204_NO_CONTENT)


class SubtemaListCreateView(APIView):
    permission_classes = [EsDocenteOAdminOLecturaEstudiante]

    def get(self, request, tema_pk):
        subtemas = Subtema.objects.filter(tema_id=tema_pk, activo=True)
        return Response(SubtemaSerializer(subtemas, many=True).data)

    def post(self, request, tema_pk):
        if request.user.rol not in ('docente', 'administrador'):
            return Response(status=status.HTTP_403_FORBIDDEN)
        if not Tema.objects.filter(pk=tema_pk, activo=True).exists():
            return Response({'detail': 'Tema no encontrado.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = SubtemaSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(tema_id=tema_pk)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ─── CU-08: Recursos académicos ──────────────────────────────────────────────

class RecursoListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = Recurso.objects.filter(activo=True).select_related('tema', 'subtema', 'creado_por')

        # CU-11: Filtros por VARK, tema y nivel
        categoria_vark = request.query_params.get('categoria_vark')
        tema_id = request.query_params.get('tema')
        nivel = request.query_params.get('nivel')
        tipo = request.query_params.get('tipo')

        if categoria_vark:
            qs = qs.filter(categoria_vark=categoria_vark)
        if tema_id:
            qs = qs.filter(tema_id=tema_id)
        if nivel:
            qs = qs.filter(nivel_complejidad=nivel)
        if tipo:
            qs = qs.filter(tipo_formato=tipo)

        serializer = RecursoSerializer(qs, many=True)
        return Response(serializer.data)

    def post(self, request):
        if request.user.rol not in ('docente', 'administrador'):
            return Response(status=status.HTTP_403_FORBIDDEN)
        serializer = RecursoSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(creado_por=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RecursoDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def _get_recurso(self, pk):
        try:
            return Recurso.objects.get(pk=pk)
        except Recurso.DoesNotExist:
            return None

    def get(self, request, pk):
        recurso = self._get_recurso(pk)
        if not recurso:
            return Response({'detail': 'Recurso no encontrado.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(RecursoSerializer(recurso).data)

    def put(self, request, pk):
        if request.user.rol not in ('docente', 'administrador'):
            return Response(status=status.HTTP_403_FORBIDDEN)
        recurso = self._get_recurso(pk)
        if not recurso:
            return Response({'detail': 'Recurso no encontrado.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = RecursoSerializer(recurso, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        if request.user.rol not in ('docente', 'administrador'):
            return Response(status=status.HTTP_403_FORBIDDEN)
        recurso = self._get_recurso(pk)
        if not recurso:
            return Response({'detail': 'Recurso no encontrado.'}, status=status.HTTP_404_NOT_FOUND)
        recurso.activo = False
        recurso.save(update_fields=['activo'])
        return Response(status=status.HTTP_204_NO_CONTENT)


# ─── CU-09: Sugerir recursos con IA ──────────────────────────────────────────

class SugerirRecursosIAView(APIView):
    permission_classes = [EsDocenteOAdmin]

    def post(self, request):
        serializer = SolicitarSugerenciaIASerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        tema = Tema.objects.get(pk=data['tema_id'])

        try:
            from .services.ia_service import sugerir_recursos_ia
            recursos_sugeridos = sugerir_recursos_ia(
                tema_nombre=tema.nombre,
                categoria_vark=data['categoria_vark'],
                nivel=data['nivel_complejidad'],
                cantidad=data['cantidad'],
            )
        except Exception as exc:
            return Response(
                {'detail': f'Error al consultar la IA: {exc}'},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        # Guardar las sugerencias en estado pendiente
        sugerencias_creadas = []
        for r in recursos_sugeridos:
            sugerencia = SugerenciaIA.objects.create(
                titulo=r.get('titulo', ''),
                url=r.get('url', ''),
                descripcion=r.get('descripcion', ''),
                justificacion_pedagogica=r.get('justificacion_pedagogica', ''),
                tema=tema,
                categoria_vark=data['categoria_vark'],
                nivel_complejidad=data['nivel_complejidad'],
                tipo_formato=r.get('tipo_formato', 'articulo'),
            )
            sugerencias_creadas.append(sugerencia)

        return Response(
            SugerenciaIASerializer(sugerencias_creadas, many=True).data,
            status=status.HTTP_201_CREATED,
        )


# ─── CU-10: Revisar y aprobar sugerencias IA ─────────────────────────────────

class SugerenciaIAListView(APIView):
    permission_classes = [EsDocenteOAdmin]

    def get(self, request):
        estado = request.query_params.get('estado', 'pendiente')
        sugerencias = SugerenciaIA.objects.filter(estado=estado).select_related('tema', 'revisado_por')
        return Response(SugerenciaIASerializer(sugerencias, many=True).data)


class SugerenciaIAAprobarView(APIView):
    permission_classes = [EsDocenteOAdmin]

    def post(self, request, pk):
        try:
            sugerencia = SugerenciaIA.objects.get(pk=pk, estado=SugerenciaIA.ESTADO_PENDIENTE)
        except SugerenciaIA.DoesNotExist:
            return Response(
                {'detail': 'Sugerencia no encontrada o ya revisada.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        recurso = Recurso.objects.create(
            titulo=sugerencia.titulo,
            url=sugerencia.url,
            descripcion=sugerencia.descripcion,
            tema=sugerencia.tema,
            categoria_vark=sugerencia.categoria_vark,
            nivel_complejidad=sugerencia.nivel_complejidad,
            tipo_formato=sugerencia.tipo_formato,
            sugerido_por_ia=True,
            validado_por=request.user,
            creado_por=request.user,
        )

        sugerencia.estado = SugerenciaIA.ESTADO_APROBADO
        sugerencia.revisado_por = request.user
        sugerencia.recurso_creado = recurso
        sugerencia.fecha_revision = timezone.now()
        sugerencia.save()

        return Response({
            'detail': f'Recurso aprobado y agregado al repositorio.',
            'recurso': RecursoSerializer(recurso).data,
        }, status=status.HTTP_200_OK)


class SugerenciaIARechazarView(APIView):
    permission_classes = [EsDocenteOAdmin]

    def post(self, request, pk):
        try:
            sugerencia = SugerenciaIA.objects.get(pk=pk, estado=SugerenciaIA.ESTADO_PENDIENTE)
        except SugerenciaIA.DoesNotExist:
            return Response(
                {'detail': 'Sugerencia no encontrada o ya revisada.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        sugerencia.estado = SugerenciaIA.ESTADO_RECHAZADO
        sugerencia.revisado_por = request.user
        sugerencia.fecha_revision = timezone.now()
        sugerencia.save()

        return Response({'detail': 'Sugerencia rechazada.'}, status=status.HTTP_200_OK)


# ─── CU-05: Banco de preguntas ───────────────────────────────────────────────

class PreguntaListCreateView(APIView):
    permission_classes = [EsDocenteOAdmin]

    def get(self, request):
        qs = Pregunta.objects.filter(activo=True).select_related('tema', 'subtema').prefetch_related('opciones')
        tema_id = request.query_params.get('tema')
        dificultad = request.query_params.get('dificultad')
        if tema_id:
            qs = qs.filter(tema_id=tema_id)
        if dificultad:
            qs = qs.filter(nivel_dificultad=dificultad)
        return Response(PreguntaSerializer(qs, many=True).data)

    def post(self, request):
        serializer = PreguntaSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(creado_por=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PreguntaDetailView(APIView):
    permission_classes = [EsDocenteOAdmin]

    def _get_pregunta(self, pk):
        try:
            return Pregunta.objects.get(pk=pk)
        except Pregunta.DoesNotExist:
            return None

    def get(self, request, pk):
        pregunta = self._get_pregunta(pk)
        if not pregunta:
            return Response({'detail': 'Pregunta no encontrada.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(PreguntaSerializer(pregunta).data)

    def put(self, request, pk):
        pregunta = self._get_pregunta(pk)
        if not pregunta:
            return Response({'detail': 'Pregunta no encontrada.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = PreguntaSerializer(pregunta, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        pregunta = self._get_pregunta(pk)
        if not pregunta:
            return Response({'detail': 'Pregunta no encontrada.'}, status=status.HTTP_404_NOT_FOUND)
        pregunta.activo = False
        pregunta.save(update_fields=['activo'])
        return Response(status=status.HTTP_204_NO_CONTENT)


# ─── Fase 4: Generar preguntas de quiz con IA ────────────────────────────────

class SugerirPreguntasIAView(APIView):
    """POST /contenido/preguntas/sugerir/ → candidatas IA (no se guardan)."""
    permission_classes = [EsDocenteOAdmin]

    def post(self, request):
        serializer = SolicitarPreguntasIASerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        tema = Tema.objects.get(pk=data['tema_id'])

        try:
            from .services.ia_service import generar_preguntas_quiz
            preguntas = generar_preguntas_quiz(
                tema_nombre=tema.nombre,
                dificultad=data['dificultad'],
                cantidad=data['cantidad'],
            )
        except Exception as exc:
            return Response(
                {'detail': f'La IA no está disponible. Puedes crear preguntas manualmente. ({exc})'},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        return Response({
            'tema': tema.id,
            'tema_nombre': tema.nombre,
            'dificultad': data['dificultad'],
            'total': len(preguntas),
            'preguntas': preguntas,  # {enunciado, explicacion, opciones:[{texto, es_correcta}]}
        }, status=status.HTTP_200_OK)


# ─── CU-07: Quizzes ──────────────────────────────────────────────────────────

class QuizObtenerPreguntasView(APIView):
    """Retorna preguntas aleatorias de un tema para que el estudiante responda."""
    permission_classes = [EsEstudiante]

    def get(self, request, tema_pk):
        if not Tema.objects.filter(pk=tema_pk, activo=True).exists():
            return Response({'detail': 'Tema no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        preguntas_qs = list(
            Pregunta.objects.filter(tema_id=tema_pk, activo=True)
            .prefetch_related('opciones')
        )

        if not preguntas_qs:
            return Response(
                {'detail': 'No hay preguntas disponibles para este tema.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        cantidad = min(PREGUNTAS_POR_QUIZ, len(preguntas_qs))
        seleccionadas = random.sample(preguntas_qs, cantidad)

        return Response({
            'tema_id': tema_pk,
            'total_preguntas': cantidad,
            'preguntas': PreguntaFrontendSerializer(seleccionadas, many=True).data,
        })


class QuizResponderView(APIView):
    """Recibe respuestas, calcula puntaje y guarda el resultado."""
    permission_classes = [EsEstudiante]

    def post(self, request):
        serializer = RespuestaQuizSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        tema_id = serializer.validated_data['tema_id']
        respuestas = serializer.validated_data['respuestas']

        detalle = []
        correctas = 0

        for resp in respuestas:
            pregunta_id = resp['pregunta_id']
            opcion_id = resp['opcion_id']

            try:
                opcion = OpcionPregunta.objects.select_related('pregunta').get(
                    pk=opcion_id, pregunta_id=pregunta_id
                )
                es_correcta = opcion.es_correcta
            except OpcionPregunta.DoesNotExist:
                es_correcta = False

            if es_correcta:
                correctas += 1

            detalle.append({
                'pregunta_id': pregunta_id,
                'opcion_id': opcion_id,
                'es_correcta': es_correcta,
            })

        total = len(respuestas)
        puntaje = correctas / total if total > 0 else 0.0

        tema = Tema.objects.get(pk=tema_id)
        resultado = ResultadoQuiz.objects.create(
            estudiante=request.user,
            tema=tema,
            puntaje=round(puntaje, 4),
            total_preguntas=total,
            respuestas_correctas=correctas,
            respuestas_json=detalle,
        )

        return Response(
            ResultadoQuizSerializer(resultado).data,
            status=status.HTTP_201_CREATED,
        )


class QuizHistorialView(APIView):
    """Historial de quizzes completados por el estudiante autenticado."""
    permission_classes = [EsEstudiante]

    def get(self, request):
        resultados = ResultadoQuiz.objects.filter(
            estudiante=request.user
        ).select_related('tema').order_by('-fecha_realizacion')
        return Response(ResultadoQuizSerializer(resultados, many=True).data)
