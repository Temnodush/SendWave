from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django.core.cache import cache

from .models import Mailing, MailingAttempt, EmailRecipient


def send_mailing(mailing):
    """
    Отправляет рассылку всем получателям.
    Возвращает словарь со статистикой.
    """
    if not mailing.can_send():
        return {
            'success': False,
            'error': 'Рассылка не может быть отправлена в данный момент',
            'sent': 0,
            'failed': 0
        }

    recipients = mailing.recipients.all()
    attempts = []
    sent_count = 0
    failed_count = 0

    for recipient in recipients:
        try:
            send_mail(
                subject=mailing.message.subject,
                message=mailing.message.body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[recipient.email],
                fail_silently=False
            )
            attempts.append(MailingAttempt(
                mailing=mailing,
                recipient=recipient,
                status='SUCCESS',
                server_response='Письмо успешно отправлено'
            ))
            sent_count += 1

        except Exception as e:
            attempts.append(MailingAttempt(
                mailing=mailing,
                recipient=recipient,
                status='FAILED',
                server_response=str(e)
            ))
            failed_count += 1

    MailingAttempt.objects.bulk_create(attempts)

    return {
        'success': True,
        'sent': sent_count,
        'failed': failed_count
    }


def get_home_stats():
    """
    Возвращает статистику для главной страницы.
    Использует кеширование.
    """
    stats = cache.get('home_stats')

    if stats is None:
        now = timezone.now()

        total_mailings = Mailing.objects.count()

        # Активные рассылки: текущее время между start_time и end_time, и is_active=True
        active_mailings = Mailing.objects.filter(
            start_time__lte=now,
            end_time__gte=now,
            is_active=True
        ).count()

        unique_clients = EmailRecipient.objects.count()

        stats = {
            'total_mailings': total_mailings,
            'active_mailings': active_mailings,
            'unique_clients': unique_clients
        }

        cache.set('home_stats', stats, 60 * 5)  # Кеш на 5 минут

    return stats


def get_user_stats(user):
    """
    Возвращает персональную статистику пользователя.
    """
    user_mailings = Mailing.objects.filter(owner=user)
    user_clients = EmailRecipient.objects.filter(owner=user)

    # Попытки отправки по рассылкам пользователя
    attempts = MailingAttempt.objects.filter(mailing__owner=user)

    return {
        'mailings_count': user_mailings.count(),
        'clients_count': user_clients.count(),
        'successful_attempts': attempts.filter(status='SUCCESS').count(),
        'failed_attempts': attempts.filter(status='FAILED').count(),
        'total_sent': attempts.count()
    }
