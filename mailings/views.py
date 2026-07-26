from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import TemplateView, ListView, DetailView, CreateView, DeleteView, UpdateView
from mailings.forms import ClientForm, MessageForm, MailingForm
from mailings.mixins import OwnerQuerysetMixin, OwnerRequiredMixin, ManagerRequiredMixin
from mailings.models import EmailRecipient, Message, Mailing, MailingAttempt
from mailings.services import get_user_stats, send_mailing, invalidate_stats_cache, invalidate_user_stats_cache, \
    get_home_stats
from django.utils import timezone




User = get_user_model()


class HomePageView(TemplateView):
    """Главная страница с публичной и персональной статистикой"""
    template_name = 'mailings/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Получаем статистику из кеша
        home_stats = get_home_stats()

        # Вычисляем success_rate
        total_attempts = home_stats.get('total_attempts', 0)
        successful_attempts = home_stats.get('successful_attempts', 0)

        if total_attempts > 0:
            success_rate = round((successful_attempts / total_attempts) * 100)
        else:
            success_rate = 99

        context['stats'] = {
            'total_users': User.objects.filter(is_active=True).count(),
            'total_mailings': home_stats['total_mailings'],
            'total_sent': total_attempts,
            'success_rate': success_rate,
            'active_mailings': home_stats['active_mailings'],
        }

        # Персональная статистика для авторизованных (тоже из кеша)
        if self.request.user.is_authenticated:
            context['user_stats'] = get_user_stats(self.request.user)

        return context


class DashboardPageView(LoginRequiredMixin, TemplateView):
    template_name = "mailings/dashboard.html"

#=======================================
# Контроллеры для EmailRecipients (Клиентов)
#=======================================

class ClientListView(LoginRequiredMixin, OwnerQuerysetMixin, ListView):
    model = EmailRecipient
    template_name = "mailings/client_list.html"
    context_object_name = "clients"
    paginate_by = 10



class ClientDetailView(LoginRequiredMixin, OwnerQuerysetMixin, DetailView):
    model = EmailRecipient
    template_name = 'mailings/client_detail.html'
    context_object_name = 'client'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Рассылки, в которых участвует клиент
        context['mailings'] = self.object.mailing_set.all()
        return context


class ClientCreateView(LoginRequiredMixin, CreateView):
    model = EmailRecipient
    form_class = ClientForm
    template_name = 'mailings/client_form.html'
    success_url = reverse_lazy('mailings:client_list')

    def form_valid(self, form):
        form.instance.owner = self.request.user
        messages.success(self.request, 'Клиент успешно добавлен')
        response = super().form_valid(form)

        # Инвалидируем кеш
        invalidate_stats_cache()
        invalidate_user_stats_cache(self.request.user.id)

        return response


class ClientDeleteView(LoginRequiredMixin, OwnerRequiredMixin, DeleteView):
    model = EmailRecipient
    template_name = 'mailings/client_confirm_delete.html'
    success_url = reverse_lazy('mailings:client_list')

    def form_valid(self, form):
        messages.success(self.request, "Клиент успешно удалён.")

        # Инвалидируем кеш перед удалением
        invalidate_stats_cache()
        invalidate_user_stats_cache(self.request.user.id)

        return super().form_valid(form)

class ClientUpdateView(LoginRequiredMixin, OwnerRequiredMixin, UpdateView):
    model = EmailRecipient
    form_class = ClientForm
    template_name = 'mailings/client_form.html'
    success_url = reverse_lazy('mailings:client_list')

    def form_valid(self, form):
        messages.success(self.request, "Данные успешно изменены.")
        return super().form_valid(form)


#===============================
# Контроллеры для сообщений.
#===============================

class MessageListView(LoginRequiredMixin, OwnerQuerysetMixin, ListView):
    """
    Список сообщений пользователя.
    """
    model = Message
    template_name = 'mailings/message_list.html'
    context_object_name = 'messages_list'  # Не 'messages' — конфликт с django messages
    paginate_by = 10


class MessageDetailView(LoginRequiredMixin, OwnerQuerysetMixin, DetailView):
    """
    Детальная информация о сообщении.
    """
    model = Message
    template_name = 'mailings/message_detail.html'
    context_object_name = 'message'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Рассылки, использующие это сообщение
        context['mailings'] = self.object.mailing_set.all()
        return context


class MessageCreateView(LoginRequiredMixin, CreateView):
    model = Message
    form_class = MessageForm
    template_name = 'mailings/message_form.html'
    success_url = reverse_lazy('mailings:message_list')

    def form_valid(self, form):
        form.instance.owner = self.request.user
        messages.success(self.request, 'Сообщение создано')
        response = super().form_valid(form)

        # Инвалидируем кеш пользователя
        invalidate_user_stats_cache(self.request.user.id)

        return response


class MessageUpdateView(LoginRequiredMixin, OwnerRequiredMixin, UpdateView):
    """
    Редактирование сообщения. Только для владельца.
    """
    model = Message
    form_class = MessageForm
    template_name = 'mailings/message_form.html'
    success_url = reverse_lazy('mailings:message_list')

    def form_valid(self, form):
        messages.success(self.request, 'Сообщение обновлено')
        return super().form_valid(form)


class MessageDeleteView(LoginRequiredMixin, OwnerRequiredMixin, DeleteView):
    model = Message
    template_name = 'mailings/message_confirm_delete.html'
    success_url = reverse_lazy('mailings:message_list')

    def form_valid(self, form):
        messages.success(self.request, 'Сообщение удалено')

        # Инвалидируем кеш
        invalidate_user_stats_cache(self.request.user.id)

        return super().form_valid(form)


#=================================================
# Рассылки
#=================================================

class MailingListView(LoginRequiredMixin, OwnerQuerysetMixin, ListView):
    """
    Список рассылок пользователя.
    Поддерживает фильтрацию по статусу через GET-параметр.
    """
    model = Mailing
    template_name = 'mailings/mailing_list.html'
    context_object_name = 'mailings'
    paginate_by = 10

    def get_queryset(self):
        qs = super().get_queryset()

        # Фильтрация по статусу (опционально)
        status_filter = self.request.GET.get('status')
        if status_filter:
            from django.utils import timezone
            now = timezone.now()

            if status_filter == 'created':
                qs = qs.filter(start_time__gt=now)
            elif status_filter == 'running':
                qs = qs.filter(start_time__lte=now, end_time__gte=now)
            elif status_filter == 'finished':
                qs = qs.filter(end_time__lt=now)

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_filter'] = self.request.GET.get('status', '')
        return context


class MailingDetailView(LoginRequiredMixin, OwnerQuerysetMixin, DetailView):
    """
    Детальная информация о рассылке.
    Показывает историю попыток отправки.
    """
    model = Mailing
    template_name = 'mailings/mailing_detail.html'
    context_object_name = 'mailing'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # История попыток (последние первыми)
        attempts = self.object.attempts.order_by('-attempt_time')[:50]
        context['attempts'] = attempts

        # Статистика
        context['success_count'] = self.object.attempts.filter(status='SUCCESS').count()
        context['failed_count'] = self.object.attempts.filter(status='FAILED').count()

        return context


class MailingCreateView(LoginRequiredMixin, CreateView):
    model = Mailing
    form_class = MailingForm
    template_name = 'mailings/mailing_form.html'
    success_url = reverse_lazy('mailings:mailing_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.owner = self.request.user
        messages.success(self.request, 'Рассылка создана')
        response = super().form_valid(form)

        # Инвалидируем кеш
        invalidate_stats_cache()
        invalidate_user_stats_cache(self.request.user.id)

        return response


class MailingUpdateView(LoginRequiredMixin, OwnerRequiredMixin, UpdateView):
    """
    Редактирование рассылки. Только для владельца.
    """
    model = Mailing
    form_class = MailingForm
    template_name = 'mailings/mailing_form.html'
    success_url = reverse_lazy('mailings:mailing_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, 'Рассылка обновлена')
        return super().form_valid(form)


class MailingDeleteView(LoginRequiredMixin, OwnerRequiredMixin, DeleteView):
    model = Mailing
    template_name = 'mailings/mailing_confirm_delete.html'
    success_url = reverse_lazy('mailings:mailing_list')

    def form_valid(self, form):
        messages.success(self.request, 'Рассылка удалена')

        # Инвалидируем кеш
        invalidate_stats_cache()
        invalidate_user_stats_cache(self.request.user.id)

        return super().form_valid(form)

# =============================================================================
# Действия с рассылками
# =============================================================================

class MailingSendView(LoginRequiredMixin, View):
    """
    Ручной запуск отправки рассылки.
    Доступно только владельцу.
    """

    def post(self, request, pk):
        mailing = get_object_or_404(Mailing, pk=pk)

        # Проверка прав
        if mailing.owner != request.user:
            messages.error(request, 'У вас нет прав на эту операцию')
            return redirect('mailings:mailing_list')

        # Проверка возможности отправки
        if not mailing.can_send():
            messages.error(
                request,
                'Рассылка не может быть отправлена. '
                'Проверьте, что текущее время находится в заданном периоде и рассылка активна.'
            )
            return redirect('mailings:mailing_detail', pk=pk)

        # Отправка
        result = send_mailing(mailing)

        if result['success']:
            messages.success(
                request,
                f"Отправка завершена. Успешно: {result['sent']}, ошибок: {result['failed']}"
            )
        else:
            messages.error(request, result['error'])

        return redirect('mailings:mailing_detail', pk=pk)


class MailingDisableView(LoginRequiredMixin, ManagerRequiredMixin, View):
    """
    Отключение рассылки менеджером.
    Устанавливает is_active = False.
    """

    def post(self, request, pk):
        mailing = get_object_or_404(Mailing, pk=pk)
        mailing.is_active = False
        mailing.save()

        messages.success(request, f'Рассылка "{mailing}" отключена')
        return redirect('mailings:mailing_list')


# =============================================================================
# Статистика пользователя
# =============================================================================


class UserStatsView(LoginRequiredMixin, TemplateView):
    """
    Персональная статистика пользователя.
    """
    template_name = 'mailings/user_stats.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['stats'] = get_user_stats(self.request.user)

        # Последние попытки отправки
        context['recent_attempts'] = MailingAttempt.objects.filter(
            mailing__owner=self.request.user
        ).order_by('-attempt_time')[:20]

        return context
