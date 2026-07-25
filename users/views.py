import os

from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.mail import send_mail
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import CreateView, FormView, TemplateView, UpdateView, DeleteView
from .forms import CustomUserCreationForm, CustomUserChangeForm
from .models import CustomUser


# Create your views here.

class RegisterView(FormView):
    template_name = 'users/register.html'
    form_class = CustomUserCreationForm
    success_url = reverse_lazy('mailings:home')

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        # self.send_welcome_email(user.email)
        return super().form_valid(form)

 # def send_welcome_email(self, user_email, from_email=os.getenv('EMAIL_HOST_USER')):
 #     subject = 'Добро пожаловать в наш сервис'
 #     message = 'Спасибо, что зарегистрировались в нашем сервисе!'
 #     recipient_list = [user_email]
 #     send_mail(subject, message, from_email, recipient_list)

class ProfileView(LoginRequiredMixin, TemplateView):
    model = CustomUser
    template_name = 'users/profile.html'
    context_object_name = 'profile_user'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user'] = self.request.user
        return context

class ProfileEditView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = CustomUser
    form_class = CustomUserChangeForm
    template_name = 'users/profile_edit.html'

    # После сохранения перенаправляем на профиль этого же пользователя
    def get_success_url(self):
        return reverse_lazy('users:profile', kwargs={'pk': self.object.pk})

    # Разрешаем редактирование только своему профилю
    def test_func(self):
        obj = self.get_object()
        return self.request.user == obj

class UserDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = CustomUser
    template_name = 'users/confirm_delete.html'  # можно не использовать, если удаление через модалку
    success_url = reverse_lazy('users:list')

    def test_func(self):
        # разрешить удаление только суперпользователю или самому себе
        return self.request.user.is_superuser or self.request.user == self.get_object()