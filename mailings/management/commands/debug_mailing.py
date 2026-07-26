from django.core.management.base import BaseCommand
from django.utils import timezone
from mailings.models import Mailing


class Command(BaseCommand):
    help = 'Отладка запланированных рассылок'

    def handle(self, *args, **options):
        now = timezone.now()
        local_now = timezone.localtime(now)

        self.stdout.write(f"🕐 Время UTC: {now}")
        self.stdout.write(f"🕐 Локальное время: {local_now}")
        self.stdout.write(f"📅 День недели: {local_now.weekday()} (0=Пн, 6=Вс)")
        self.stdout.write(f"📅 День месяца: {local_now.day}")
        self.stdout.write("-" * 50)

        mailings = Mailing.objects.filter(is_active=True)

        for mailing in mailings:
            self.stdout.write(f"\n📧 Рассылка: {mailing}")
            self.stdout.write(f"   Период: {mailing.period}")
            self.stdout.write(f"   Статус: {mailing.status}")
            self.stdout.write(f"   start_time: {mailing.start_time}")
            self.stdout.write(f"   end_time: {mailing.end_time}")
            self.stdout.write(f"   send_time: {mailing.send_time}")
            self.stdout.write(f"   weekdays: {mailing.weekdays}")
            self.stdout.write(f"   day_of_month: {mailing.day_of_month}")
            self.stdout.write(f"   last_sent_at: {mailing.last_sent_at}")
            self.stdout.write(f"   can_send(): {mailing.can_send()}")

            self.stdout.write(f"\n   --- Проверка should_send_now() ---")

            if not mailing.can_send():
                self.stdout.write(self.style.ERROR("   ❌ can_send() = False"))
                continue

            # Проверка для разовой рассылки
            if mailing.period == 'once':
                if mailing.last_sent_at is None:
                    self.stdout.write(self.style.SUCCESS("   ✅ Разовая, ещё не отправлялась"))
                else:
                    self.stdout.write(self.style.ERROR("   ❌ Разовая, уже отправлялась"))
                continue

            # Используем ЛОКАЛЬНОЕ время для проверки
            current_time = local_now.time()

            # Проверка времени отправки
            if mailing.send_time:
                self.stdout.write(f"   Текущее локальное время: {current_time.hour}:{current_time.minute:02d}")
                self.stdout.write(f"   Время отправки: {mailing.send_time.hour}:{mailing.send_time.minute:02d}")

                if current_time.hour != mailing.send_time.hour:
                    self.stdout.write(
                        self.style.ERROR(f"   ❌ Час не совпадает: {current_time.hour} != {mailing.send_time.hour}"))
                    continue

                minute_diff = abs(current_time.minute - mailing.send_time.minute)
                if minute_diff > 10:
                    self.stdout.write(
                        self.style.ERROR(f"   ❌ Минуты отличаются более чем на 10: разница {minute_diff}"))
                    continue

                self.stdout.write(self.style.SUCCESS("   ✅ Время подходит"))

            # Проверка last_sent_at
            if mailing.last_sent_at:
                local_last_sent = timezone.localtime(mailing.last_sent_at)
                if local_last_sent.date() == local_now.date():
                    self.stdout.write(self.style.ERROR(f"   ❌ Уже отправлялась сегодня в {local_last_sent.time()}"))
                    continue
                else:
                    self.stdout.write(
                        self.style.SUCCESS(f"   ✅ Сегодня ещё не отправлялась (последняя: {local_last_sent.date()})"))
            else:
                self.stdout.write(self.style.SUCCESS("   ✅ Никогда не отправлялась"))

            # Проверка дня недели для еженедельной
            if mailing.period == 'weekly':
                current_weekday = local_now.weekday()
                self.stdout.write(f"   Текущий день недели: {current_weekday}")
                self.stdout.write(f"   Выбранные дни: {mailing.weekdays}")
                if current_weekday in mailing.weekdays:
                    self.stdout.write(self.style.SUCCESS("   ✅ День недели подходит"))
                else:
                    self.stdout.write(self.style.ERROR("   ❌ День недели не подходит"))
                    continue

            # Проверка дня месяца для ежемесячной
            if mailing.period == 'monthly':
                self.stdout.write(f"   Текущий день месяца: {local_now.day}")
                self.stdout.write(f"   Выбранный день: {mailing.day_of_month}")
                if local_now.day == mailing.day_of_month:
                    self.stdout.write(self.style.SUCCESS("   ✅ День месяца подходит"))
                else:
                    self.stdout.write(self.style.ERROR("   ❌ День месяца не подходит"))
                    continue

            self.stdout.write(self.style.SUCCESS("\n   ✅✅✅ ДОЛЖНА ОТПРАВИТЬСЯ ✅✅✅"))
            self.stdout.write(f"   should_send_now() = {mailing.should_send_now()}")
