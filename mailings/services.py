from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django.core.cache import cache

from .models import Mailing, MailingAttempt, EmailRecipient


# Время жизни кеша (из settings или 15 минут по умолчанию)
CACHE_TTL = getattr(settings, 'CACHE_TTL', 60 * 15)


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

    # Bulk create для эффективности
    MailingAttempt.objects.bulk_create(attempts)

    # Обновляем время последней отправки
    mailing.last_sent_at = timezone.now()
    mailing.save(update_fields=['last_sent_at'])

    # Инвалидируем кеш после отправки
    invalidate_stats_cache()
    invalidate_user_stats_cache(mailing.owner.id)

    return {
        'success': True,
        'sent': sent_count,
        'failed': failed_count
    }


def process_scheduled_mailings():
    """
    Обрабатывает все запланированные рассылки.
    Вызывается периодически планировщиком.
    """
    now = timezone.now()

    mailings = Mailing.objects.filter(
        is_active=True,
        start_time__lte=now,
        end_time__gte=now
    )

    results = {
        'processed': 0,
        'sent': 0,
        'skipped': 0,
        'errors': []
    }

    for mailing in mailings:
        results['processed'] += 1

        if mailing.should_send_now():
            try:
                result = send_mailing(mailing)
                if result['success']:
                    results['sent'] += 1
                    print(f"✅ Отправлена рассылка: {mailing} (успешно: {result['sent']}, ошибок: {result['failed']})")
                else:
                    results['errors'].append(f"{mailing}: {result['error']}")
            except Exception as e:
                results['errors'].append(f"{mailing}: {str(e)}")
        else:
            results['skipped'] += 1

    return results


def get_home_stats():
    """
    Возвращает статистику для главной страницы.
    Кешируется в Redis.
    """
    cache_key = 'home_stats'
    stats = cache.get(cache_key)

    if stats is None:
        now = timezone.now()

        total_mailings = Mailing.objects.count()
        active_mailings = Mailing.objects.filter(
            start_time__lte=now,
            end_time__gte=now,
            is_active=True
        ).count()
        unique_clients = EmailRecipient.objects.count()

        # Статистика попыток
        total_attempts = MailingAttempt.objects.count()
        successful_attempts = MailingAttempt.objects.filter(status='SUCCESS').count()

        stats = {
            'total_mailings': total_mailings,
            'active_mailings': active_mailings,
            'unique_clients': unique_clients,
            'total_attempts': total_attempts,
            'successful_attempts': successful_attempts,
        }

        cache.set(cache_key, stats, CACHE_TTL)

    return stats


def get_user_stats(user):
    """
    Возвращает персональную статистику пользователя.
    Кешируется в Redis.
    """
    cache_key = f'user_stats_{user.id}'
    stats = cache.get(cache_key)

    if stats is None:
        user_mailings = Mailing.objects.filter(owner=user)
        user_clients = EmailRecipient.objects.filter(owner=user)
        attempts = MailingAttempt.objects.filter(mailing__owner=user)

        stats = {
            'mailings_count': user_mailings.count(),
            'clients_count': user_clients.count(),
            'successful_attempts': attempts.filter(status='SUCCESS').count(),
            'failed_attempts': attempts.filter(status='FAILED').count(),
            'total_sent': attempts.count()
        }

        cache.set(cache_key, stats, CACHE_TTL)

    return stats


def invalidate_stats_cache():
    """Инвалидирует кеш общей статистики"""
    cache.delete('home_stats')


def invalidate_user_stats_cache(user_id):
    """Инвалидирует кеш статистики пользователя"""
    cache.delete(f'user_stats_{user_id}')


def invalidate_all_user_stats_cache():
    """Инвалидирует кеш статистики всех пользователей"""
    # Для Redis можно использовать паттерн
    try:
        cache.delete_pattern('user_stats_*')
    except AttributeError:
        # Если delete_pattern не поддерживается
        pass
