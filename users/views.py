import os

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse_lazy, reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.views import View
from django.views.generic import FormView, TemplateView, UpdateView, DeleteView, ListView

from .forms import CustomUserCreationForm, CustomUserChangeForm
from .models import CustomUser


class RegisterView(FormView):
    """Регистрация с подтверждением email"""
    template_name = 'users/register.html'
    form_class = CustomUserCreationForm
    success_url = reverse_lazy('users:registration_complete')

    def form_valid(self, form):
        user = form.save(commit=False)
        user.is_active = False  # Пользователь неактивен до подтверждения
        user.save()

        # Генерируем токен
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))

        # Отправляем письмо
        confirm_url = self.request.build_absolute_uri(
            reverse('users:confirm_email', kwargs={'uidb64': uid, 'token': token})
        )
        send_mail(
            'Подтвердите email — SendWave',
            f'Здравствуйте!\n\nДля завершения регистрации перейдите по ссылке:\n{confirm_url}\n\nЕсли вы не регистрировались, проигнорируйте это письмо.',
            settings.DEFAULT_FROM_EMAIL,
            [user.email]
        )

        return super().form_valid(form)


class RegistrationCompleteView(TemplateView):
    """Страница после регистрации — проверьте почту"""
    template_name = 'users/registration_complete.html'


class EmailConfirmView(View):
    """Подтверждение email по ссылке из письма"""

    def get(self, request, uidb64, token):
        try:
            uid = urlsafe_base64_decode(uidb64).decode()
            user = CustomUser.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, CustomUser.DoesNotExist):
            user = None

        if user is not None and default_token_generator.check_token(user, token):
            user.is_active = True
            user.email_verified = True
            user.save()
            messages.success(request, 'Email подтверждён! Теперь вы можете войти.')
            return redirect('users:login')
        else:
            messages.error(request, 'Ссылка недействительна или устарела.')
            return redirect('users:register')


class ProfileView(LoginRequiredMixin, TemplateView):
    """Профиль пользователя"""
    template_name = 'users/profile.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['profile_user'] = get_object_or_404(CustomUser, pk=self.kwargs['pk'])
        return context


class ProfileEditView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Редактирование профиля"""
    model = CustomUser
    form_class = CustomUserChangeForm
    template_name = 'users/profile_edit.html'

    def get_success_url(self):
        return reverse_lazy('users:profile', kwargs={'pk': self.object.pk})

    def test_func(self):
        obj = self.get_object()
        return self.request.user == obj


class UserDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """Удаление пользователя"""
    model = CustomUser
    template_name = 'users/confirm_delete.html'
    success_url = reverse_lazy('users:user_list')

    def test_func(self):
        return self.request.user.is_superuser or self.request.user == self.get_object()


class UserListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """Список пользователей — только для менеджеров"""
    model = CustomUser
    template_name = 'users/user_list.html'
    context_object_name = 'users'
    paginate_by = 20

    def test_func(self):
        return self.request.user.is_manager or self.request.user.is_superuser

    def get_queryset(self):
        return CustomUser.objects.filter(is_superuser=False).order_by('-date_joined')


class UserBlockView(LoginRequiredMixin, UserPassesTestMixin, View):
    """Блокировка/разблокировка пользователя — только для менеджеров"""

    def test_func(self):
        return self.request.user.is_manager or self.request.user.is_superuser

    def post(self, request, pk):
        user = get_object_or_404(CustomUser, pk=pk)

        if user == request.user or user.is_superuser:
            messages.error(request, 'Нельзя заблокировать этого пользователя')
            return redirect('users:user_list')

        user.is_active = not user.is_active
        user.save()

        status = 'разблокирован' if user.is_active else 'заблокирован'
        messages.success(request, f'Пользователь {user.email} {status}')

        return redirect('users:user_list')
