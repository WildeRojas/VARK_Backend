from django.db.models import Q
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from .models import (
    ConfiguracionTestVARK,
    PerfilVARK,
    PreguntaVARK,
    SesionTestVARK,
    Usuario,
)
from .permissions import EsAdmin
from .serializers import (
    CambiarPasswordSerializer,
    ConfiguracionTestVARKSerializer,
    LoginSerializer,
    MeUpdateSerializer,
    PerfilVARKSerializer,
    PreguntaVARKSerializer,
    RegistroSerializer,
    RespuestasTestSerializer,
    UsuarioAdminSerializer,
    UsuarioSerializer,
)
from .services.vark_service import (
    calcular_vector_vark,
    generar_preguntas_candidatas,
    generar_test_vark,
)


# ─── CU-01: Registro ─────────────────────────────────────────────────────────

class RegistroView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegistroSerializer(data=request.data)
        if serializer.is_valid():
            usuario = serializer.save()
            return Response(
                UsuarioSerializer(usuario).data,
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ─── CU-02: Autenticación ────────────────────────────────────────────────────

class LoginView(TokenObtainPairView):
    permission_classes = [AllowAny]
    serializer_class = LoginSerializer


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return Response(
                {'detail': 'El token de refresco es requerido.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(
                {'detail': 'Sesión cerrada correctamente.'},
                status=status.HTTP_200_OK,
            )
        except Exception:
            return Response(
                {'detail': 'Token inválido o ya expirado.'},
                status=status.HTTP_400_BAD_REQUEST,
            )


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UsuarioSerializer(request.user).data)

    def patch(self, request):
        """Fase 7: el usuario edita su propio perfil (no su rol)."""
        serializer = MeUpdateSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(UsuarioSerializer(request.user).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        """Fase 7: el usuario elimina (desactiva) su propia cuenta."""
        usuario = request.user
        usuario.is_active = False
        usuario.save(update_fields=['is_active'])
        return Response({'detail': 'Cuenta desactivada.'}, status=status.HTTP_200_OK)


class CambiarPasswordView(APIView):
    """POST /accounts/me/cambiar-password/ → cambiar la propia contraseña."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CambiarPasswordSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        usuario = request.user
        if not usuario.check_password(serializer.validated_data['password_actual']):
            return Response(
                {'password_actual': 'La contraseña actual es incorrecta.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        usuario.set_password(serializer.validated_data['password_nueva'])
        usuario.save(update_fields=['password'])
        return Response({'detail': 'Contraseña actualizada correctamente.'})


# ─── CU-03: Test VARK ────────────────────────────────────────────────────────

class VARKGenerarTestView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        usuario = request.user

        if usuario.rol != usuario.ROL_ESTUDIANTE:
            return Response(
                {'detail': 'Solo los estudiantes pueden tomar el test VARK.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        perfil, _ = PerfilVARK.objects.get_or_create(usuario=usuario)
        if perfil.test_completado:
            return Response(
                {'detail': 'Ya completaste el test VARK.', 'completado': True},
                status=status.HTTP_200_OK,
            )

        # Generar preguntas (Groq con fallback estático)
        preguntas_completas, fuente = generar_test_vark()

        # Invalidar sesiones anteriores incompletas y crear una nueva
        SesionTestVARK.objects.filter(usuario=usuario, completado=False).delete()
        sesion = SesionTestVARK.objects.create(
            usuario=usuario,
            preguntas_json=preguntas_completas,
        )

        # Enviar preguntas al frontend SIN revelar el campo 'estilo'
        preguntas_frontend = [
            {
                'id': p['id'],
                'enunciado': p['enunciado'],
                'opciones': [
                    {'id': o['id'], 'texto': o['texto']}
                    for o in p['opciones']
                ],
            }
            for p in preguntas_completas
        ]

        return Response({
            'sesion_id': sesion.id,
            'fuente': fuente,
            'total_preguntas': len(preguntas_frontend),
            'preguntas': preguntas_frontend,
        }, status=status.HTTP_200_OK)


class VARKCompletarTestView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        usuario = request.user

        serializer = RespuestasTestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        sesion_id = serializer.validated_data['sesion_id']
        respuestas = serializer.validated_data['respuestas']

        try:
            sesion = SesionTestVARK.objects.get(
                id=sesion_id, usuario=usuario, completado=False
            )
        except SesionTestVARK.DoesNotExist:
            return Response(
                {'detail': 'Sesión de test no encontrada o ya completada.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        vector = calcular_vector_vark(sesion.preguntas_json, respuestas)

        perfil, _ = PerfilVARK.objects.get_or_create(usuario=usuario)
        perfil.puntaje_visual = vector['V']
        perfil.puntaje_auditivo = vector['A']
        perfil.puntaje_lectura = vector['R']
        perfil.puntaje_kinestesico = vector['K']
        perfil.test_completado = True
        perfil.fecha_test = timezone.now()
        perfil.save()

        sesion.completado = True
        sesion.save()

        return Response({
            'detail': 'Test completado exitosamente.',
            'perfil_vark': PerfilVARKSerializer(perfil).data,
        }, status=status.HTTP_200_OK)


class PerfilVARKView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            perfil = request.user.perfil_vark
            return Response(PerfilVARKSerializer(perfil).data)
        except PerfilVARK.DoesNotExist:
            return Response(
                {'detail': 'Perfil VARK no encontrado.'},
                status=status.HTTP_404_NOT_FOUND,
            )


# ─── Fase 2: Gestión de usuarios (solo Administrador) ────────────────────────

class UsuarioListCreateView(APIView):
    permission_classes = [EsAdmin]

    def get(self, request):
        qs = Usuario.objects.all().order_by('-fecha_registro')
        rol = request.query_params.get('rol')
        activo = request.query_params.get('activo')
        buscar = request.query_params.get('buscar')
        if rol:
            qs = qs.filter(rol=rol)
        if activo in ('true', 'false'):
            qs = qs.filter(is_active=(activo == 'true'))
        if buscar:
            qs = qs.filter(
                Q(nombre__icontains=buscar)
                | Q(apellido__icontains=buscar)
                | Q(email__icontains=buscar)
            )
        return Response(UsuarioAdminSerializer(qs, many=True).data)

    def post(self, request):
        serializer = UsuarioAdminSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UsuarioDetailView(APIView):
    permission_classes = [EsAdmin]

    def _get(self, pk):
        try:
            return Usuario.objects.get(pk=pk)
        except Usuario.DoesNotExist:
            return None

    def get(self, request, pk):
        usuario = self._get(pk)
        if not usuario:
            return Response({'detail': 'Usuario no encontrado.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(UsuarioAdminSerializer(usuario).data)

    def patch(self, request, pk):
        usuario = self._get(pk)
        if not usuario:
            return Response({'detail': 'Usuario no encontrado.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = UsuarioAdminSerializer(usuario, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        usuario = self._get(pk)
        if not usuario:
            return Response({'detail': 'Usuario no encontrado.'}, status=status.HTTP_404_NOT_FOUND)
        if usuario.pk == request.user.pk:
            return Response(
                {'detail': 'No puedes desactivar tu propia cuenta.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        # Soft delete
        usuario.is_active = False
        usuario.save(update_fields=['is_active'])
        return Response(status=status.HTTP_204_NO_CONTENT)


class ResetPasswordView(APIView):
    """POST /accounts/usuarios/<pk>/reset-password/  → el admin asigna una nueva contraseña."""
    permission_classes = [EsAdmin]

    def post(self, request, pk):
        try:
            usuario = Usuario.objects.get(pk=pk)
        except Usuario.DoesNotExist:
            return Response({'detail': 'Usuario no encontrado.'}, status=status.HTTP_404_NOT_FOUND)
        nueva = request.data.get('password_nueva') or request.data.get('password')
        if not nueva or len(nueva) < 8:
            return Response(
                {'detail': 'La nueva contraseña debe tener al menos 8 caracteres.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        usuario.set_password(nueva)
        usuario.save(update_fields=['password'])
        return Response({'detail': 'Contraseña restablecida correctamente.'})


# ─── Fase 3: Edición del test VARK por el administrador ───────────────────────

class VARKConfigView(APIView):
    """GET/PUT /accounts/vark/config/ → configuración del test (singleton)."""
    permission_classes = [EsAdmin]

    def get(self, request):
        config = ConfiguracionTestVARK.get_solo()
        return Response(ConfiguracionTestVARKSerializer(config).data)

    def put(self, request):
        config = ConfiguracionTestVARK.get_solo()
        serializer = ConfiguracionTestVARKSerializer(config, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VARKGenerarPreguntasView(APIView):
    """POST /accounts/vark/generar-preguntas/ → candidatas IA (no se guardan)."""
    permission_classes = [EsAdmin]

    def post(self, request):
        cantidad = int(request.data.get('cantidad') or 10)
        contexto = request.data.get('contexto') or ''
        if not contexto:
            contexto = ConfiguracionTestVARK.get_solo().contexto_tematico
        candidatas, fuente = generar_preguntas_candidatas(cantidad, contexto)
        return Response({
            'fuente': fuente,
            'total': len(candidatas),
            'preguntas': candidatas,  # incluyen 'estilo' para que el admin valide
        })


class VARKBancoListCreateView(APIView):
    """GET/POST /accounts/vark/banco/ → listar / crear preguntas del banco."""
    permission_classes = [EsAdmin]

    def get(self, request):
        qs = PreguntaVARK.objects.all().prefetch_related('opciones')
        activo = request.query_params.get('activo')
        if activo in ('true', 'false'):
            qs = qs.filter(activo=(activo == 'true'))
        return Response(PreguntaVARKSerializer(qs, many=True).data)

    def post(self, request):
        serializer = PreguntaVARKSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VARKBancoDetailView(APIView):
    """GET/PUT/DELETE /accounts/vark/banco/<pk>/ → editar / desactivar pregunta."""
    permission_classes = [EsAdmin]

    def _get(self, pk):
        try:
            return PreguntaVARK.objects.prefetch_related('opciones').get(pk=pk)
        except PreguntaVARK.DoesNotExist:
            return None

    def get(self, request, pk):
        pregunta = self._get(pk)
        if not pregunta:
            return Response({'detail': 'Pregunta no encontrada.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(PreguntaVARKSerializer(pregunta).data)

    def put(self, request, pk):
        pregunta = self._get(pk)
        if not pregunta:
            return Response({'detail': 'Pregunta no encontrada.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = PreguntaVARKSerializer(
            pregunta, data=request.data, partial=True, context={'request': request}
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        pregunta = self._get(pk)
        if not pregunta:
            return Response({'detail': 'Pregunta no encontrada.'}, status=status.HTTP_404_NOT_FOUND)
        # Soft delete: desactivar para no romper sesiones/históricos
        pregunta.activo = False
        pregunta.save(update_fields=['activo'])
        return Response(status=status.HTTP_204_NO_CONTENT)


class VARKPreviewView(APIView):
    """GET /accounts/vark/preview/ → genera un test de ejemplo según la config (sin guardar)."""
    permission_classes = [EsAdmin]

    def get(self, request):
        preguntas, fuente = generar_test_vark()
        # Mostramos el estilo de cada opción para que el admin lo revise
        return Response({
            'fuente': fuente,
            'total_preguntas': len(preguntas),
            'preguntas': preguntas,
        })
