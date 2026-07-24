from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Entrena los modelos de ML (clasificador de utilidad + clustering) y guarda métricas.'

    def add_arguments(self, parser):
        parser.add_argument('--clusters', type=int, default=4, help='Número de clusters de estudiantes.')
        parser.add_argument('--test-size', type=float, default=0.25, help='Proporción del conjunto de prueba.')

    def handle(self, *args, **options):
        from apps.recomendacion.services.ml.train import entrenar

        self.stdout.write('Entrenando modelos de ML...')
        try:
            metricas = entrenar(
                test_size=options['test_size'],
                n_clusters=options['clusters'],
            )
        except ValueError as exc:
            self.stderr.write(self.style.ERROR(str(exc)))
            return

        clf = metricas['clasificador']
        clu = metricas['clustering']
        self.stdout.write(self.style.SUCCESS('✓ Entrenamiento completado.'))
        self.stdout.write(
            f"  Clasificador de utilidad: muestras={clf['n_muestras']} "
            f"accuracy={clf['accuracy']} precision={clf['precision']} "
            f"recall={clf['recall']} f1={clf['f1']} (baseline={clf['baseline_mayoria']})"
        )
        self.stdout.write(
            f"  Clustering: k={clu['n_clusters']} silhouette={clu['silhouette']} "
            f"tamaños={clu['tamanos']}"
        )
