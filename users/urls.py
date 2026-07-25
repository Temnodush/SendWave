from django.urls import path
from django.views.generic import TemplateView

from . import views
from .forms import CustomAuthenticationForm
from .views import RegisterView, ProfileView, ProfileEditView
from django.contrib.auth.views import LoginView, LogoutView

app_name = 'users'

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(template_name="users/login.html", authentication_form=CustomAuthenticationForm ), name='login'),
    path('logout/', LogoutView.as_view(next_page='mailings:home'), name='logout'),
    path('profile/<int:pk>', views.ProfileView.as_view(), name='profile'),
    path('profile/edit/<int:pk>', views.ProfileEditView.as_view(), name='profile_edit'),
    path('delete/<int:pk>/', views.UserDeleteView.as_view(), name='delete_user'),
]