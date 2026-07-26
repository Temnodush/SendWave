from django.urls import path, reverse_lazy
from django.contrib.auth.views import (
    LoginView, LogoutView,
    PasswordResetView, PasswordResetDoneView,
    PasswordResetConfirmView, PasswordResetCompleteView
)

from . import views
from .forms import CustomAuthenticationForm

app_name = 'users'

urlpatterns = [
    # Регистрация и подтверждение email
    path('register/', views.RegisterView.as_view(), name='register'),
    path('registration-complete/', views.RegistrationCompleteView.as_view(), name='registration_complete'),
    path('confirm-email/<uidb64>/<token>/', views.EmailConfirmView.as_view(), name='confirm_email'),

    # Вход/Выход
    path('login/', LoginView.as_view(
        template_name="users/login.html",
        authentication_form=CustomAuthenticationForm
    ), name='login'),
    path('logout/', LogoutView.as_view(next_page='mailings:home'), name='logout'),

    # Профиль
    path('profile/<int:pk>/', views.ProfileView.as_view(), name='profile'),
    path('profile/edit/<int:pk>/', views.ProfileEditView.as_view(), name='profile_edit'),
    path('delete/<int:pk>/', views.UserDeleteView.as_view(), name='delete_user'),

    # Восстановление пароля — указываем полные пути
    path('password-reset/', PasswordResetView.as_view(
        template_name='users/password_reset.html',
        email_template_name='users/password_reset_email.html',
        success_url=reverse_lazy('users:password_reset_done')
    ), name='password_reset'),

    path('password-reset/done/', PasswordResetDoneView.as_view(
        template_name='users/password_reset_done.html'
    ), name='password_reset_done'),

    path('password-reset-confirm/<uidb64>/<token>/', PasswordResetConfirmView.as_view(
        template_name='users/password_reset_confirm.html',
        success_url=reverse_lazy('users:password_reset_complete')
    ), name='password_reset_confirm'),

    path('password-reset-complete/', PasswordResetCompleteView.as_view(
        template_name='users/password_reset_complete.html'
    ), name='password_reset_complete'),

    # Управление пользователями (для менеджеров)
    path('list/', views.UserListView.as_view(), name='user_list'),
    path('block/<int:pk>/', views.UserBlockView.as_view(), name='block_user'),
]
