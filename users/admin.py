from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = (
    'email', 'username', 'first_name', 'last_name', 'is_manager', 'is_active', 'is_staff', 'date_joined')
    list_filter = ('is_active', 'is_staff', 'is_manager', 'date_joined')
    search_fields = ('email', 'username', 'first_name', 'last_name')
    ordering = ('-date_joined',)
    list_editable = ('is_manager', 'is_active')  # Можно менять прямо в списке

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Личная информация', {'fields': ('username', 'first_name', 'last_name', 'phone_number', 'avatar')}),
        ('Права доступа', {'fields': (
        'is_active', 'is_staff', 'is_superuser', 'is_manager', 'email_verified', 'groups', 'user_permissions')}),
        ('Важные даты', {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'password1', 'password2', 'is_manager'),
        }),
    )
