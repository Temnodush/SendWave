from django.urls import path
from . import views

app_name = 'mailings'

urlpatterns = [
    # Главные страницы
    path('', views.HomePageView.as_view(), name='home'),
    path('dashboard/', views.DashboardPageView.as_view(), name='dashboard'),

    # Клиенты
    path('dashboard/clients/', views.ClientListView.as_view(), name='client_list'),
    path('dashboard/clients/<int:pk>/', views.ClientDetailView.as_view(), name='client_detail'),
    path('dashboard/clients/create/', views.ClientCreateView.as_view(), name='client_create'),
    path('dashboard/clients/<int:pk>/update/', views.ClientUpdateView.as_view(), name='client_update'),
    path('dashboard/clients/<int:pk>/delete/', views.ClientDeleteView.as_view(), name='client_delete'),

    # Сообщения
    path('dashboard/messages/', views.MessageListView.as_view(), name='message_list'),
    path('dashboard/messages/<int:pk>/', views.MessageDetailView.as_view(), name='message_detail'),
    path('dashboard/messages/create/', views.MessageCreateView.as_view(), name='message_create'),
    path('dashboard/messages/<int:pk>/update/', views.MessageUpdateView.as_view(), name='message_update'),
    path('dashboard/messages/<int:pk>/delete/', views.MessageDeleteView.as_view(), name='message_delete'),

    # Рассылки
    path('dashboard/mailings/', views.MailingListView.as_view(), name='mailing_list'),
    path('dashboard/mailings/<int:pk>/', views.MailingDetailView.as_view(), name='mailing_detail'),
    path('dashboard/mailings/create/', views.MailingCreateView.as_view(), name='mailing_create'),
    path('dashboard/mailings/<int:pk>/update/', views.MailingUpdateView.as_view(), name='mailing_update'),
    path('dashboard/mailings/<int:pk>/delete/', views.MailingDeleteView.as_view(), name='mailing_delete'),

    # Действия
    path('dashboard/mailings/<int:pk>/send/', views.MailingSendView.as_view(), name='mailing_send'),
    path('dashboard/mailings/<int:pk>/disable/', views.MailingDisableView.as_view(), name='mailing_disable'),

    # Статистика
    path('dashboard/stats/', views.UserStatsView.as_view(), name='user_stats'),
    ]