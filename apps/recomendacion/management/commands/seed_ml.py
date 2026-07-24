"""
Genera datos sintéticos **con correlación real** para entrenar el ML.

La señal aprendible se codifica así:
  - Cada estudiante tiene un estilo VARK dominante (vector sesgado + ruido).
  - Hace más clic y permanece más tiempo en recursos **afines** a su estilo.
  - Valora como "útil" los recursos afines con mayor probabilidad.
  - Sus quizzes rinden mejor cuanto más consumió recursos afines.

Los datos quedan asociados a estudiantes con email `ml.<i>@est.vark.edu`, para poder
limpiarlos con --flush sin tocar el seed principal.
"""

import random

from django.core.management.base import BaseCommand
from django.db import transaction

EMAIL_PREFIX = 'ml.'
EMAIL_DOMINIO = '@est.vark.edu'

VARK = ['V', 'A', 'R', 'K']
TIPOS_POR_CAT = {'V': 'video', 'A': 'video', 'R': 'documento', 'K': 'ejercicio'}
NIVELES = ['basico', 'intermedio', 'avanzado']


def _vector_sesgado(dominante, rng):
    """Vector VARK con un estilo dominante + ruido, normalizado a suma 1."""
    base = {k: rng.uniform(0.05, 0.20) for k in VARK}
    base[dominante] += rng.uniform(0.55, 0.85)
    total = sum(base.values())
    return {k: round(v / total, 4) for k, v in base.items()}


class Command(BaseCommand):
    help = 'Genera datos sintéticos correlacionados con el VARK para entrenar el ML.'

    def add_arguments(self, parser):
        parser.add_argument('--estudiantes', type=int, default=60)
        parser.add_argument('--seed', type=int, default=42)
        parser.add_argument('--flush', action='store_true', help='Elimina los datos ML previos antes de generar.')

    @transaction.atomic
    def handle(self, *args, **options):
        from apps.accounts.models import PerfilVARK, Usuario
        from apps.contenido.models import Recurso, ResultadoQuiz, Tema
        from apps.recomendacion.models import (
            EventoClickstream, HistorialPerfilVARK, ValoracionRecurso,
        )

        rng = random.Random(options['seed'])

        if options['flush']:
            viejos = Usuario.objects.filter(email__startswith=EMAIL_PREFIX, email__endswith=EMAIL_DOMINIO)
            n = viejos.count()
            viejos.delete()  # cascada borra perfiles, clickstream, valoraciones, quizzes
            self.stdout.write(self.style.WARNING(f'Eliminados {n} estudiantes ML previos.'))

        temas = list(Tema.objects.filter(activo=True))
        if not temas:
            self.stderr.write(self.style.ERROR('No hay temas. Corre primero seed_data.'))
            return

        # ── 1) Asegurar catálogo: ≥2 recursos por (tema, categoría VARK) ──────────
        catalogo = self._asegurar_catalogo(Recurso, temas, rng)
        self.stdout.write(f'Catálogo de recursos disponible: {len(catalogo)}')

        # ── 2) Crear estudiantes con perfil sesgado ───────────────────────────────
        n_est = options['estudiantes']
        estudiantes = []
        for i in range(n_est):
            dominante = VARK[i % 4]
            email = f'{EMAIL_PREFIX}{i}{EMAIL_DOMINIO}'
            usuario, creado = Usuario.objects.get_or_create(
                email=email,
                defaults={'nombre': f'EstML{i}', 'apellido': dominante, 'rol': 'estudiante'},
            )
            if creado:
                usuario.set_password('vark1234')
                usuario.save()
            vector = _vector_sesgado(dominante, rng)
            perfil, _ = PerfilVARK.objects.get_or_create(usuario=usuario)
            perfil.puntaje_visual = vector['V']
            perfil.puntaje_auditivo = vector['A']
            perfil.puntaje_lectura = vector['R']
            perfil.puntaje_kinestesico = vector['K']
            perfil.test_completado = True
            perfil.save()
            estudiantes.append((usuario, vector, dominante))

        # ── 3) Simular interacciones correlacionadas ──────────────────────────────
        clics_creados = 0
        valoraciones_creadas = 0
        quizzes_creados = 0
        eventos = []

        for usuario, vector, dominante in estudiantes:
            consumo_por_tema = {}  # tema_id -> suma de afinidad consumida
            for recurso in catalogo:
                afinidad = vector[recurso.categoria_vark]  # 0..~0.85
                p_click = max(0.05, min(0.95, 0.10 + 1.4 * afinidad))
                if rng.random() > p_click:
                    continue

                # Clics y permanencia escalados por afinidad
                n_clics = 1 + int(rng.random() * 4 * afinidad + 0.5)
                for _ in range(n_clics):
                    eventos.append(EventoClickstream(
                        estudiante=usuario, recurso=recurso, tipo_evento='clic',
                    ))
                clics_creados += n_clics

                permanencia = int(rng.gauss(60 + 240 * afinidad, 25))
                permanencia = max(5, permanencia)
                eventos.append(EventoClickstream(
                    estudiante=usuario, recurso=recurso,
                    tipo_evento='permanencia', duracion_segundos=permanencia,
                ))

                consumo_por_tema[recurso.tema_id] = consumo_por_tema.get(recurso.tema_id, 0.0) + afinidad

                # Valoración correlacionada con la afinidad
                p_util = max(0.05, min(0.95, 0.10 + 1.3 * afinidad))
                valoracion = 'util' if rng.random() < p_util else 'no_util'
                ValoracionRecurso.objects.update_or_create(
                    estudiante=usuario, recurso=recurso,
                    defaults={'valoracion': valoracion},
                )
                valoraciones_creadas += 1

            # ── Quizzes correlacionados con el consumo afín ──────────────────────
            for tema in temas:
                consumo = consumo_por_tema.get(tema.id, 0.0)
                base = 0.45 + min(0.45, consumo * 0.35) + rng.uniform(-0.1, 0.1)
                puntaje = max(0.0, min(1.0, base))
                total_p = 10
                correctas = int(round(puntaje * total_p))
                ResultadoQuiz.objects.create(
                    estudiante=usuario, tema=tema,
                    puntaje=round(puntaje, 4), total_preguntas=total_p,
                    respuestas_correctas=correctas, respuestas_json=[],
                )
                quizzes_creados += 1

            # ── Un par de snapshots de evolución del perfil ──────────────────────
            anterior = {k: round(vector[k] + rng.uniform(-0.05, 0.05), 4) for k in VARK}
            HistorialPerfilVARK.objects.create(
                estudiante=usuario, vector_anterior=anterior, vector_nuevo=vector,
                origen='clickstream',
            )

        EventoClickstream.objects.bulk_create(eventos, batch_size=500)

        self.stdout.write(self.style.SUCCESS('✓ Datos sintéticos generados.'))
        self.stdout.write(
            f'  estudiantes={len(estudiantes)} clics={clics_creados} '
            f'valoraciones={valoraciones_creadas} quizzes={quizzes_creados}'
        )
        self.stdout.write('  Ahora ejecuta: python manage.py entrenar_ml')

    def _asegurar_catalogo(self, Recurso, temas, rng):
        """Garantiza ≥2 recursos activos por (tema, categoría VARK). Devuelve la lista completa."""
        catalogo = []
        for tema in temas:
            for cat in VARK:
                existentes = list(Recurso.objects.filter(
                    tema=tema, categoria_vark=cat, activo=True, url_valida=True,
                ))
                faltan = max(0, 2 - len(existentes))
                for j in range(faltan):
                    nivel = NIVELES[(j) % len(NIVELES)]
                    r = Recurso.objects.create(
                        titulo=f'[ML] {tema.nombre} {cat} #{j + 1}',
                        url=f'https://example.com/ml/{tema.id}/{cat}/{j}',
                        descripcion='Recurso sintético para entrenamiento ML.',
                        tema=tema, categoria_vark=cat, nivel_complejidad=nivel,
                        tipo_formato=TIPOS_POR_CAT[cat], activo=True, url_valida=True,
                    )
                    existentes.append(r)
                catalogo.extend(existentes)
        return catalogo
