from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from users.models import CustomUser


class EmailRecipient(models.Model):
    """ Модель получателя рассылки """


    email = models.EmailField(verbose_name="Email получателя")
    fullname = models.CharField(max_length=100, verbose_name="ФИО получателя")
    comment = models.TextField(blank=True, verbose_name="Сообщение")
    owner = models.ForeignKey(CustomUser, on_delete=models.CASCADE , verbose_name="Отправитель")


    def __str__(self):
        return self.email

    class Meta:
        verbose_name = 'получатель'
        verbose_name_plural = 'получатели'
        ordering = ['email']

class Message(models.Model):
    """Модель сообщения рассылки"""
    subject = models.CharField(max_length=200, verbose_name="Тема сообщения")
    body = models.TextField(verbose_name="Сообщение")
    owner = models.ForeignKey(CustomUser, on_delete=models.CASCADE , verbose_name="Отправитель")

    def __str__(self):
        return self.subject

    class Meta:
        verbose_name = "сообщение"
        verbose_name_plural = "сообщения"


class Mailing(models.Model):
    # Периодичность
    PERIOD_ONCE = 'once'
    PERIOD_DAILY = 'daily'
    PERIOD_WEEKLY = 'weekly'
    PERIOD_MONTHLY = 'monthly'

    PERIOD_CHOICES = [
        (PERIOD_ONCE, 'Разовая'),
        (PERIOD_DAILY, 'Ежедневно'),
        (PERIOD_WEEKLY, 'Еженедельно'),
        (PERIOD_MONTHLY, 'Ежемесячно'),
    ]

    # Дни недели
    WEEKDAY_CHOICES = [
        (0, 'Понедельник'),
        (1, 'Вторник'),
        (2, 'Среда'),
        (3, 'Четверг'),
        (4, 'Пятница'),
        (5, 'Суббота'),
        (6, 'Воскресенье'),
    ]

    # Основные поля
    start_time = models.DateTimeField(verbose_name="Дата и время начала")
    end_time = models.DateTimeField(verbose_name="Дата и время окончания")
    message = models.ForeignKey(Message, on_delete=models.CASCADE, verbose_name="Сообщение")
    recipients = models.ManyToManyField(EmailRecipient, verbose_name="Получатели")
    owner = models.ForeignKey(CustomUser, on_delete=models.CASCADE, verbose_name="Владелец")
    is_active = models.BooleanField(default=True, verbose_name="Активна")

    # Поля для периодичности
    period = models.CharField(
        max_length=20,
        choices=PERIOD_CHOICES,
        default=PERIOD_ONCE,
        verbose_name="Периодичность"
    )
    send_time = models.TimeField(
        null=True,
        blank=True,
        verbose_name="Время отправки",
        help_text="Время суток для автоматической отправки"
    )
    weekdays = models.JSONField(
        default=list,
        blank=True,
        verbose_name="Дни недели",
        help_text="Для еженедельной рассылки"
    )
    day_of_month = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        verbose_name="День месяца",
        help_text="Для ежемесячной рассылки (1-31)"
    )
    last_sent_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Последняя отправка"
    )

    @property
    def status(self):
        """Вычисляет текущий статус рассылки"""
        from django.utils import timezone
        now = timezone.now()

        # Для разовой рассылки: если отправлена — завершена
        if self.period == self.PERIOD_ONCE and self.last_sent_at is not None:
            return 'Завершена'

        if now < self.start_time:
            return 'Создана'
        elif self.start_time <= now <= self.end_time:
            return 'Запущена'
        else:
            return 'Завершена'

    def can_send(self):
        """Проверяет, можно ли сейчас отправить рассылку"""
        from django.utils import timezone
        now = timezone.now()
        return self.is_active and self.start_time <= now <= self.end_time

    def clean(self):
        """Валидация модели"""
        if self.start_time and self.end_time:
            if self.start_time >= self.end_time:
                raise ValidationError("Дата начала должна быть раньше даты окончания")

        # Для всех типов кроме разовой нужно время отправки
        if self.period != self.PERIOD_ONCE and not self.send_time:
            raise ValidationError("Укажите время отправки для периодической рассылки")

        # Для ежедневной — можно выбрать несколько дней (или все)
        if self.period == self.PERIOD_DAILY:
            if not self.weekdays:
                self.weekdays = [0, 1, 2, 3, 4, 5, 6]

        # Для еженедельной — нужен ровно один день
        if self.period == self.PERIOD_WEEKLY:
            if not self.weekdays or len(self.weekdays) != 1:
                raise ValidationError("Для еженедельной рассылки выберите один день недели")

        # Для ежемесячной — нужен день месяца
        if self.period == self.PERIOD_MONTHLY:
            if not self.day_of_month or not (1 <= self.day_of_month <= 31):
                raise ValidationError("Для ежемесячной рассылки укажите день месяца (1-31)")

    def should_send_now(self):
        """Проверяет, нужно ли отправить рассылку сейчас"""
        if not self.can_send():
            return False

        from django.utils import timezone

        now = timezone.now()
        local_now = timezone.localtime(now)

        # Разовая рассылка — отправляем если ещё не отправляли
        if self.period == self.PERIOD_ONCE:
            return self.last_sent_at is None

        # Проверяем время отправки (с допуском 10 минут)
        if self.send_time:
            current_time = local_now.time()
            send_hour = self.send_time.hour
            send_minute = self.send_time.minute

            if current_time.hour != send_hour:
                return False
            if abs(current_time.minute - send_minute) > 10:
                return False

        # Проверяем, не отправляли ли уже сегодня
        if self.last_sent_at:
            local_last_sent = timezone.localtime(self.last_sent_at)
            if local_last_sent.date() == local_now.date():
                return False

        # Ежедневная — проверяем выбранные дни недели
        if self.period == self.PERIOD_DAILY:
            current_weekday = local_now.weekday()
            return current_weekday in self.weekdays

        # Еженедельная — проверяем день недели
        if self.period == self.PERIOD_WEEKLY:
            current_weekday = local_now.weekday()
            return current_weekday in self.weekdays

        # Ежемесячная — проверяем день месяца
        if self.period == self.PERIOD_MONTHLY:
            return local_now.day == self.day_of_month

        return False

    def get_next_send_time(self):
        """Вычисляет время следующей отправки"""
        from django.utils import timezone
        from datetime import timedelta

        if not self.can_send() or self.period == self.PERIOD_ONCE:
            return None

        if not self.send_time:
            return None

        now = timezone.now()

        # Базовое время — сегодня в указанное время
        next_send = now.replace(
            hour=self.send_time.hour,
            minute=self.send_time.minute,
            second=0,
            microsecond=0
        )

        # Если время уже прошло сегодня, начинаем с завтра
        if next_send <= now:
            next_send += timedelta(days=1)

        if self.period == self.PERIOD_DAILY:
            # Ищем ближайший подходящий день
            for _ in range(7):
                if next_send.weekday() in self.weekdays:
                    return next_send
                next_send += timedelta(days=1)
            return next_send

        if self.period == self.PERIOD_WEEKLY:
            # Ищем ближайший подходящий день недели
            for _ in range(7):
                if next_send.weekday() in self.weekdays:
                    return next_send
                next_send += timedelta(days=1)
            return None

        if self.period == self.PERIOD_MONTHLY:
            # Устанавливаем нужный день месяца
            try:
                next_send = next_send.replace(day=self.day_of_month)
                if next_send <= now:
                    # Переходим на следующий месяц
                    if next_send.month == 12:
                        next_send = next_send.replace(year=next_send.year + 1, month=1)
                    else:
                        next_send = next_send.replace(month=next_send.month + 1)
                return next_send
            except ValueError:
                return None

        return None

    def __str__(self):
        return f"{self.message.subject} ({self.get_period_display()})"

    class Meta:
        verbose_name = 'рассылка'
        verbose_name_plural = 'рассылки'
        ordering = ['-start_time']


class MailingAttempt(models.Model):
    ATTEMPT_CHOICES = [
        ('SUCCESS', 'Успешно'),
        ('FAILED', 'Не успешно')
    ]

    mailing = models.ForeignKey(Mailing, on_delete=models.CASCADE, related_name='attempts')
    recipient = models.ForeignKey(EmailRecipient, on_delete=models.CASCADE)
    attempt_time = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=ATTEMPT_CHOICES, default='FAILED', verbose_name='Статус')
    server_response = models.TextField(blank=True)

    def __str__(self):
        return f'{self.mailing} — {self.recipient} — {self.status}'

    class Meta:
        verbose_name = "Попытка отправки"
        verbose_name_plural = "Попытки отправки"
        ordering = ['-attempt_time']