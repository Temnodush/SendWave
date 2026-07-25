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
    """Модель рассылки"""

    start_time = models.DateTimeField(verbose_name="Дата начала")
    end_time = models.DateTimeField(verbose_name="Дата окончания")
    message = models.ForeignKey(Message, on_delete=models.CASCADE, verbose_name="Текст сообщения")
    recipients = models.ManyToManyField(EmailRecipient, verbose_name="Получатели")
    owner = models.ForeignKey(CustomUser, on_delete=models.CASCADE , verbose_name="Отправитель")
    is_active = models.BooleanField(default=True, verbose_name="Состояние")

    class Meta:
        verbose_name = "рассылка"
        verbose_name_plural = "рассылки"
        ordering = ['-start_time']

    def clean(self):
        """ Валидация создания рассылки по дате начала и окончания """
        if self.start_time and self.end_time:
            if self.start_time >= self.end_time:
                raise ValidationError("Дата начала должна быть раньше даты окончания")
            if self.start_time < timezone.now():
                raise ValidationError("Дата начала не может быть в прошлом")

    def can_send(self):
        now = timezone.now()
        return self.is_active and self.start_time <= now <= self.end_time

    @property
    def status(self):
        now = timezone.now()
        if now < self.start_time:
            return 'Создана'
        elif self.start_time <= now <= self.end_time:
            return 'Запущена'
        else:
            return 'Завершена'

class MailingAttempt(models.Model):
    """ Модель попытки рассылки """
    ATTEMPT_CHOICES = [
        ('SUCCESS', 'Успешно'),
        ('FAILED', 'Не успешно')
    ]

    mailing = models.ForeignKey(Mailing, on_delete=models.CASCADE, related_name='attempts')
    recipient = models.ForeignKey(EmailRecipient, on_delete=models.CASCADE)
    attempt_time = models.DateTimeField(auto_now=True, verbose_name="Время попытки")
    status = models.CharField(max_length=10 ,choices=ATTEMPT_CHOICES, default='FAILED', verbose_name='Статус')
    server_response = models.TextField(blank=True)

    def __str__(self):
        return f'{self.mailing} статус {self.status}'

    class Meta:
        verbose_name = "Попытка отправки"
        verbose_name_plural = "Попытки отправки"
        ordering = ['attempt_time']