"""
Genera datos sintéticos realistas y consistentes para el Sistema VARK.

Uso:
    python manage.py seed_data            # crea/asegura los datos
    python manage.py seed_data --flush    # borra los datos sintéticos antes de crear

Crea: usuarios (admin/docentes/estudiantes), perfiles VARK, temas y subtemas
(Números, Cadenas, Vectores, Matrices), recursos, banco de preguntas, resultados
de quizzes, eventos de clickstream, recomendaciones, valoraciones, historial de
perfil, configuración del motor, un experimento A/B y notificaciones.

Contraseña de todos los usuarios: vark1234
"""
import random
import unicodedata
from datetime import timedelta

from django.core.management.base import BaseCommand


def slug(texto):
    """Normaliza a ASCII en minúsculas para construir correos válidos."""
    nfkd = unicodedata.normalize('NFKD', texto)
    return ''.join(c for c in nfkd if not unicodedata.combining(c)).lower()
from django.db import transaction
from django.utils import timezone

PASSWORD = 'vark1234'

# ─── Datos base ───────────────────────────────────────────────────────────────

TEMAS = [
    ('Números', 'Tipos numéricos, operadores y aritmética en Python', [
        ('Tipos numéricos', 'int, float, complex y conversiones'),
        ('Operadores aritméticos', 'Suma, división entera, módulo y potencias'),
    ]),
    ('Cadenas', 'Manipulación de cadenas de texto (str) en Python', [
        ('Métodos de cadena', 'upper, lower, strip, split, join'),
        ('Slicing y formateo', 'Rebanadas, f-strings y concatenación'),
    ]),
    ('Vectores', 'Listas y arreglos unidimensionales', [
        ('Operaciones con listas', 'Indexado, append, len y comprensión'),
        ('Recorridos', 'for, enumerate y acumuladores'),
    ]),
    ('Matrices', 'Estructuras bidimensionales (listas de listas)', [
        ('Acceso a matrices', 'Indexado fila/columna'),
        ('Recorrido anidado', 'Dobles bucles y transposición'),
    ]),
]

# Recursos por tema: (titulo, url, descripcion, vark, nivel, tipo)
RECURSOS = {
    'Números': [
        ('Tipos de datos numéricos en Python', 'https://www.youtube.com/watch?v=khKv-8q7YmY',
         'Video con animaciones que explica int, float y complex con ejemplos visuales.',
         'V', 'basico', 'video'),
        ('Operadores aritméticos — Real Python', 'https://realpython.com/python-numbers/',
         'Artículo detallado con tablas sobre operadores, precisión y redondeo.',
         'R', 'intermedio', 'articulo'),
        ('Podcast: Aritmética y precisión en punto flotante', 'https://podcasts.example.com/vark/punto-flotante',
         'Episodio que explica por qué 0.1 + 0.2 != 0.3 mediante analogías auditivas.',
         'A', 'intermedio', 'documento'),
        ('Ejercicios de números en Python', 'https://www.w3resource.com/python-exercises/python-basic-exercises.php',
         'Set progresivo de ejercicios prácticos sobre operaciones numéricas.',
         'K', 'basico', 'ejercicio'),
    ],
    'Cadenas': [
        ('Métodos de cadenas visualizados', 'https://www.youtube.com/watch?v=k9TUPpGqYTo',
         'Video que muestra paso a paso upper, strip, split y join.',
         'V', 'basico', 'video'),
        ('Guía oficial de str — docs.python.org', 'https://docs.python.org/3/library/stdtypes.html#text-sequence-type-str',
         'Documentación oficial con todos los métodos de cadenas de Python 3.',
         'R', 'intermedio', 'articulo'),
        ('Audio: f-strings y formateo de texto', 'https://podcasts.example.com/vark/fstrings',
         'Explicación auditiva del formateo moderno de cadenas con f-strings.',
         'A', 'basico', 'documento'),
        ('Ejercicios interactivos de cadenas', 'https://exercism.org/tracks/python/exercises',
         'Retos prácticos con validación automática sobre manipulación de strings.',
         'K', 'intermedio', 'ejercicio'),
    ],
    'Vectores': [
        ('Listas en Python — Guía visual', 'https://www.youtube.com/watch?v=ohCDWZgNIU0',
         'Video con diagramas que explica indexado, append y comprensión de listas.',
         'V', 'basico', 'video'),
        ('Comprensión de listas — Real Python', 'https://realpython.com/list-comprehension-python/',
         'Artículo estructurado sobre list comprehensions con ejemplos.',
         'R', 'avanzado', 'articulo'),
        ('Recorridos con enumerate (audio)', 'https://podcasts.example.com/vark/enumerate',
         'Episodio que narra cómo recorrer listas con for y enumerate.',
         'A', 'intermedio', 'documento'),
        ('Laboratorio: manipulación de vectores', 'https://www.hackerrank.com/domains/python',
         'Laboratorio práctico para dominar operaciones con listas.',
         'K', 'intermedio', 'ejercicio'),
    ],
    'Matrices': [
        ('Matrices con listas de listas (video)', 'https://www.youtube.com/watch?v=svnkA2GVrPU',
         'Video que visualiza el acceso fila/columna en matrices bidimensionales.',
         'V', 'intermedio', 'video'),
        ('Recorrido de matrices — artículo', 'https://www.geeksforgeeks.org/python-matrix/',
         'Artículo con ejemplos de dobles bucles y transposición de matrices.',
         'R', 'avanzado', 'articulo'),
        ('Audio: pensar en 2 dimensiones', 'https://podcasts.example.com/vark/matrices-2d',
         'Explicación auditiva de cómo modelar problemas con matrices.',
         'A', 'avanzado', 'documento'),
        ('Ejercicios de matrices', 'https://www.codewars.com/kata/search/python?q=matrix',
         'Colección de katas para practicar operaciones con matrices.',
         'K', 'avanzado', 'ejercicio'),
    ],
}

# Banco de preguntas: tema -> [(enunciado, dificultad, [opciones], idx_correcta)]
PREGUNTAS = {
    'Números': [
        ('¿Qué excepción lanza Python al dividir un entero entre cero?', 'media',
         ['Retorna 0', 'Retorna infinito', 'ZeroDivisionError', 'Retorna None'], 2),
        ('¿Cuál NO es un tipo numérico en Python?', 'facil',
         ['int', 'float', 'char', 'complex'], 2),
        ('¿Qué operador devuelve el resto de una división?', 'facil',
         ['/', '//', '%', '**'], 2),
        ('¿Resultado de 7 // 2 en Python?', 'media',
         ['3.5', '3', '4', '3.0'], 1),
    ],
    'Cadenas': [
        ('¿Qué método convierte una cadena a mayúsculas?', 'facil',
         ['toUpper()', 'upper()', 'toUpperCase()', 'capitalize()'], 1),
        ('¿Qué operador concatena cadenas en Python?', 'facil',
         ['&', '.', '+', '*'], 2),
        ('¿Qué produce "Python"[1:4]?', 'media',
         ['"Pyt"', '"yth"', '"ytho"', '"tho"'], 1),
        ('¿Qué método elimina espacios al inicio y final?', 'facil',
         ['strip()', 'trim()', 'clean()', 'remove()'], 0),
    ],
    'Vectores': [
        ('¿Complejidad de acceder a una lista por índice?', 'media',
         ['O(n)', 'O(log n)', 'O(1)', 'O(n²)'], 2),
        ('¿Qué función devuelve la longitud de una lista?', 'facil',
         ['size()', 'length()', 'count()', 'len()'], 3),
        ('¿Qué método agrega un elemento al final?', 'facil',
         ['add()', 'append()', 'push()', 'insert()'], 1),
        ('¿Qué devuelve [1,2,3][-1]?', 'media',
         ['1', '3', 'Error', 'None'], 1),
    ],
    'Matrices': [
        ('¿Cómo se accede a la fila 2, columna 3 (índices base 0)?', 'dificil',
         ['m[2][3]', 'm[1][2]', 'm(2,3)', 'm.get(2,3)'], 1),
        ('Una matriz en Python suele representarse como…', 'facil',
         ['una cadena', 'una lista de listas', 'un entero', 'un set'], 1),
        ('¿Cuántos elementos tiene una matriz 3×4?', 'media',
         ['7', '12', '34', '9'], 1),
        ('¿Qué estructura se usa para recorrer una matriz completa?', 'media',
         ['un solo for', 'dos for anidados', 'while infinito', 'recursión obligatoria'], 1),
    ],
}

# Estudiantes: (nombre, apellido, estilo dominante)
ESTUDIANTES = [
    ('Lucía', 'Fernández', 'V'),
    ('Mateo', 'Rojas', 'R'),
    ('Valentina', 'Gómez', 'K'),
    ('Sebastián', 'Mamani', 'A'),
    ('Camila', 'Quispe', 'V'),
    ('Diego', 'Vargas', 'R'),
    ('Sofía', 'Choque', 'K'),
    ('Joaquín', 'Flores', 'A'),
    ('Antonella', 'Cruz', 'V'),
    ('Benjamín', 'Apaza', 'R'),
    ('Renata', 'Salinas', 'K'),
    ('Thiago', 'Condori', 'V'),
]

VARK_KEYS = {'V': 'puntaje_visual', 'A': 'puntaje_auditivo',
             'R': 'puntaje_lectura', 'K': 'puntaje_kinestesico'}


def perfil_para_estilo(dominante):
    """Genera un vector VARK plausible con el estilo dado como dominante."""
    base = {'V': 0.2, 'A': 0.2, 'R': 0.2, 'K': 0.2}
    for k in base:
        base[k] = round(random.uniform(0.10, 0.30), 3)
    base[dominante] = round(random.uniform(0.45, 0.70), 3)
    total = sum(base.values())
    return {k: round(v / total, 3) for k, v in base.items()}


class Command(BaseCommand):
    help = 'Crea datos sintéticos realistas para el Sistema de Recomendación VARK.'

    def add_arguments(self, parser):
        parser.add_argument('--flush', action='store_true',
                            help='Borra los datos antes de volver a crearlos.')

    @transaction.atomic
    def handle(self, *args, **opts):
        from apps.accounts.models import PerfilVARK, Usuario
        from apps.analitica.models import (AsignacionExperimento, ExperimentoAB,
                                           Notificacion)
        from apps.contenido.models import (OpcionPregunta, Pregunta, Recurso,
                                           ResultadoQuiz, Subtema, SugerenciaIA, Tema)
        from apps.recomendacion.models import (ConfiguracionMotor, EventoClickstream,
                                               HistorialPerfilVARK, Recomendacion,
                                               ValoracionRecurso)

        if opts['flush']:
            self.stdout.write('Borrando datos previos…')
            for model in (Notificacion, AsignacionExperimento, ExperimentoAB,
                          ValoracionRecurso, HistorialPerfilVARK, Recomendacion,
                          EventoClickstream, ResultadoQuiz, OpcionPregunta, Pregunta,
                          SugerenciaIA, Recurso, Subtema, Tema):
                model.objects.all().delete()
            Usuario.objects.exclude(is_superuser=True).delete()

        random.seed(42)
        now = timezone.now()

        # ── Usuarios ────────────────────────────────────────────────────────
        admin, _ = Usuario.objects.get_or_create(
            email='admin@vark.edu',
            defaults=dict(nombre='Ada', apellido='Lovelace', rol='administrador',
                          is_staff=True, is_superuser=True),
        )
        admin.set_password(PASSWORD); admin.save()

        docentes = []
        for nombre, apellido in [('Carlos', 'García'), ('Marta', 'Martínez')]:
            email = f'{slug(nombre)}.{slug(apellido)}@vark.edu'
            doc, _ = Usuario.objects.get_or_create(
                email=email, defaults=dict(nombre=nombre, apellido=apellido, rol='docente'))
            doc.set_password(PASSWORD); doc.save()
            docentes.append(doc)

        estudiantes = []
        for nombre, apellido, estilo in ESTUDIANTES:
            email = f'{slug(nombre)}.{slug(apellido)}@est.vark.edu'
            est, _ = Usuario.objects.get_or_create(
                email=email, defaults=dict(nombre=nombre, apellido=apellido, rol='estudiante'))
            est.set_password(PASSWORD); est.save()

            vector = perfil_para_estilo(estilo)
            perfil, _ = PerfilVARK.objects.get_or_create(usuario=est)
            for letra, campo in VARK_KEYS.items():
                setattr(perfil, campo, vector[letra])
            perfil.test_completado = True
            perfil.fecha_test = now - timedelta(days=random.randint(20, 40))
            perfil.save()
            estudiantes.append((est, estilo, vector))

        self.stdout.write(self.style.SUCCESS(
            f'Usuarios: 1 admin, {len(docentes)} docentes, {len(estudiantes)} estudiantes'))

        # ── Temas y subtemas ────────────────────────────────────────────────
        temas = {}
        for orden, (nombre, desc, subs) in enumerate(TEMAS):
            tema, _ = Tema.objects.get_or_create(
                nombre=nombre, defaults=dict(descripcion=desc, orden=orden))
            temas[nombre] = tema
            for so, (sn, sd) in enumerate(subs):
                Subtema.objects.get_or_create(
                    tema=tema, nombre=sn, defaults=dict(descripcion=sd, orden=so))

        # ── Recursos ────────────────────────────────────────────────────────
        recursos_por_tema = {}
        for tema_nombre, lista in RECURSOS.items():
            tema = temas[tema_nombre]
            creados = []
            for (titulo, url, descripcion, vark, nivel, tipo) in lista:
                rec, _ = Recurso.objects.get_or_create(
                    titulo=titulo,
                    defaults=dict(
                        url=url, descripcion=descripcion, tema=tema,
                        categoria_vark=vark, nivel_complejidad=nivel, tipo_formato=tipo,
                        creado_por=random.choice(docentes), validado_por=random.choice(docentes),
                    ),
                )
                creados.append(rec)
            recursos_por_tema[tema_nombre] = creados

        todos_recursos = [r for lst in recursos_por_tema.values() for r in lst]
        self.stdout.write(self.style.SUCCESS(
            f'Temas: {len(temas)} · Recursos: {len(todos_recursos)}'))

        # ── Banco de preguntas ──────────────────────────────────────────────
        for tema_nombre, lista in PREGUNTAS.items():
            tema = temas[tema_nombre]
            for (enunciado, dif, opciones, idx) in lista:
                if Pregunta.objects.filter(enunciado=enunciado, tema=tema).exists():
                    continue
                preg = Pregunta.objects.create(
                    enunciado=enunciado, tema=tema, nivel_dificultad=dif,
                    creado_por=random.choice(docentes))
                for i, texto in enumerate(opciones):
                    OpcionPregunta.objects.create(
                        pregunta=preg, texto=texto, es_correcta=(i == idx))

        # ── Sugerencias IA pendientes (CU-09/10) ────────────────────────────
        SugerenciaIA.objects.get_or_create(
            titulo='Visualizador de algoritmos sobre listas',
            defaults=dict(
                url='https://visualgo.net/en/list', descripcion='Herramienta visual interactiva.',
                justificacion_pedagogica='Refuerza el aprendizaje visual mostrando el estado de la lista paso a paso.',
                tema=temas['Vectores'], categoria_vark='V', nivel_complejidad='intermedio',
                tipo_formato='video'),
        )
        SugerenciaIA.objects.get_or_create(
            titulo='Podcast: pensar en matrices',
            defaults=dict(
                url='https://podcasts.example.com/vark/matriz-mental',
                descripcion='Serie auditiva sobre razonamiento bidimensional.',
                justificacion_pedagogica='Apoya a estudiantes auditivos a interiorizar el modelo de matrices.',
                tema=temas['Matrices'], categoria_vark='A', nivel_complejidad='avanzado',
                tipo_formato='documento'),
        )

        # ── Actividad por estudiante: quizzes, clickstream, recomendaciones ──
        origen_inicial = HistorialPerfilVARK.ORIGEN_TEST_INICIAL
        for est, estilo, vector in estudiantes:
            # Historial: punto inicial (test) + un ajuste por clickstream
            anterior = {'V': 0.25, 'A': 0.25, 'R': 0.25, 'K': 0.25}
            HistorialPerfilVARK.objects.get_or_create(
                estudiante=est, origen=origen_inicial,
                defaults=dict(vector_anterior=anterior, vector_nuevo=vector,
                              fecha=now - timedelta(days=30)))
            intermedio = {k: round((anterior[k] + vector[k]) / 2, 3) for k in anterior}
            HistorialPerfilVARK.objects.get_or_create(
                estudiante=est, origen=HistorialPerfilVARK.ORIGEN_CLICKSTREAM,
                defaults=dict(vector_anterior=intermedio, vector_nuevo=vector,
                              fecha=now - timedelta(days=10)))

            # Quizzes: 1-2 temas resueltos
            for tema_nombre in random.sample(list(temas), k=random.randint(1, 2)):
                tema = temas[tema_nombre]
                total = 4
                correctas = random.randint(2, 4)
                if ResultadoQuiz.objects.filter(estudiante=est, tema=tema).exists():
                    continue
                ResultadoQuiz.objects.create(
                    estudiante=est, tema=tema, puntaje=round(correctas / total, 4),
                    total_preguntas=total, respuestas_correctas=correctas,
                    respuestas_json=[], )

            # Clickstream: clics sobre recursos afines al estilo dominante
            afines = [r for r in todos_recursos if r.categoria_vark == estilo] or todos_recursos
            for rec in random.sample(afines, k=min(3, len(afines))):
                for _ in range(random.randint(1, 4)):
                    EventoClickstream.objects.create(
                        estudiante=est, recurso=rec, tipo_evento='clic')
                EventoClickstream.objects.create(
                    estudiante=est, recurso=rec, tipo_evento='permanencia',
                    duracion_segundos=random.randint(30, 600))

            # Recomendaciones guardadas (CU-12/13)
            tema_rec = temas[random.choice(list(temas))]
            recs_tema = recursos_por_tema[tema_rec.nombre]
            for rec in random.sample(recs_tema, k=min(2, len(recs_tema))):
                punt = round(random.uniform(0.55, 0.95), 3)
                Recomendacion.objects.get_or_create(
                    estudiante=est, recurso=rec, tema=tema_rec,
                    defaults=dict(
                        puntuacion=punt, vista=random.choice([True, False]),
                        vector_vark_snapshot=vector,
                        justificacion=(
                            f'Te recomendamos este recurso porque tu perfil muestra afinidad '
                            f'con el estilo {estilo} y el formato {rec.get_tipo_formato_display().lower()} '
                            f'encaja con tu forma de aprender {tema_rec.nombre.lower()}.')))

            # Valoraciones
            for rec in random.sample(afines, k=min(2, len(afines))):
                ValoracionRecurso.objects.get_or_create(
                    estudiante=est, recurso=rec,
                    defaults=dict(valoracion=random.choice(['util', 'util', 'no_util']),
                                  comentario=random.choice(
                                      ['Muy claro', 'Me ayudó bastante', 'Demasiado largo', ''])))

        # ── Configuración del motor (singleton) ─────────────────────────────
        ConfiguracionMotor.obtener()

        # ── Experimento A/B con asignaciones ────────────────────────────────
        exp, _ = ExperimentoAB.objects.get_or_create(
            nombre='Personalización VARK vs. control — Semestre I',
            defaults=dict(
                descripcion='Compara el engagement de estudiantes con recomendación '
                            'personalizada (experimental) frente a recursos sin personalizar (control).',
                estado='activo', creado_por=admin))
        mitad = len(estudiantes) // 2
        for i, (est, _, _) in enumerate(estudiantes):
            grupo = 'experimental' if i < mitad else 'control'
            AsignacionExperimento.objects.get_or_create(
                experimento=exp, estudiante=est, defaults=dict(grupo=grupo))

        # ── Notificaciones para algunos estudiantes ─────────────────────────
        recurso_demo = todos_recursos[0]
        for est, _, _ in estudiantes[:5]:
            Notificacion.objects.get_or_create(
                destinatario=est, titulo=f'Nuevo recurso disponible: {recurso_demo.titulo}',
                defaults=dict(
                    tipo='nuevo_recurso',
                    mensaje=f'Hemos agregado un recurso sobre "{recurso_demo.tema.nombre}" '
                            f'que encaja con tu perfil de aprendizaje.',
                    recurso=recurso_demo, leida=False))

        self.stdout.write(self.style.SUCCESS('\n✓ Datos sintéticos creados correctamente.'))
        self.stdout.write('\nCredenciales (contraseña: %s):' % PASSWORD)
        self.stdout.write('  • Admin:   admin@vark.edu')
        self.stdout.write('  • Docente: carlos.garcia@vark.edu / marta.martinez@vark.edu')
        self.stdout.write('  • Alumno:  lucia.fernandez@est.vark.edu  (y 11 más en @est.vark.edu)')
