from django.core.management.base import BaseCommand
from django.core.cache import cache


class Command(BaseCommand):
    help = 'Очищает весь кеш Redis'

    def add_arguments(self, parser):
        parser.add_argument(
            '--stats',
            action='store_true',
            help='Очистить только кеш статистики',
        )

    def handle(self, *args, **options):
        if options['stats']:
            # Очищаем только статистику
            cache.delete('home_stats')
            self.stdout.write(self.style.SUCCESS('✅ Кеш статистики очищен'))
        else:
            # Очищаем весь кеш
            cache.clear()
            self.stdout.write(self.style.SUCCESS('✅ Весь кеш очищен'))
