from django.core.management.base import BaseCommand
from mailings.services import process_scheduled_mailings


class Command(BaseCommand):
    help = 'Обрабатывает и отправляет запланированные рассылки'

    def handle(self, *args, **options):
        self.stdout.write('🚀 Запуск обработки запланированных рассылок...')

        results = process_scheduled_mailings()

        self.stdout.write(f"📊 Обработано рассылок: {results['processed']}")
        self.stdout.write(f"✅ Отправлено: {results['sent']}")
        self.stdout.write(f"⏭️ Пропущено: {results['skipped']}")

        if results['errors']:
            self.stdout.write(self.style.ERROR(f"❌ Ошибок: {len(results['errors'])}"))
            for error in results['errors']:
                self.stdout.write(self.style.ERROR(f"   - {error}"))
        else:
            self.stdout.write(self.style.SUCCESS('✨ Все рассылки обработаны без ошибок'))
