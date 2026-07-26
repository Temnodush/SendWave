from django.contrib import admin
from .models import EmailRecipient, Message, Mailing, MailingAttempt


@admin.register(EmailRecipient)
class EmailRecipientAdmin(admin.ModelAdmin):
    list_display = ('email', 'fullname', 'owner', 'get_mailings_count')
    list_filter = ('owner',)
    search_fields = ('email', 'fullname')
    list_per_page = 20

    def get_mailings_count(self, obj):
        return obj.mailing_set.count()

    get_mailings_count.short_description = 'В рассылках'


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('subject', 'owner', 'short_body', 'get_mailings_count')
    list_filter = ('owner',)
    search_fields = ('subject', 'body')
    list_per_page = 20

    def short_body(self, obj):
        return obj.body[:50] + '...' if len(obj.body) > 50 else obj.body

    short_body.short_description = 'Текст'

    def get_mailings_count(self, obj):
        return obj.mailing_set.count()

    get_mailings_count.short_description = 'Используется'


@admin.register(Mailing)
class MailingAdmin(admin.ModelAdmin):
    list_display = (
    'message', 'get_status', 'period', 'start_time', 'end_time', 'is_active', 'owner', 'recipients_count')
    list_filter = ('is_active', 'period', 'owner')
    search_fields = ('message__subject',)
    filter_horizontal = ('recipients',)
    list_per_page = 20
    date_hierarchy = 'start_time'
    list_editable = ('is_active',)  # Можно включать/выключать прямо в списке

    readonly_fields = ('last_sent_at',)

    fieldsets = (
        ('Основное', {
            'fields': ('message', 'recipients', 'owner', 'is_active')
        }),
        ('Период', {
            'fields': ('start_time', 'end_time')
        }),
        ('Расписание', {
            'fields': ('period', 'send_time', 'weekdays', 'day_of_month'),
            'classes': ('collapse',)  # Сворачиваемая секция
        }),
        ('Служебное', {
            'fields': ('last_sent_at',),
            'classes': ('collapse',)
        }),
    )

    def recipients_count(self, obj):
        return obj.recipients.count()

    recipients_count.short_description = 'Получателей'

    def get_status(self, obj):
        return obj.status

    get_status.short_description = 'Статус'


@admin.register(MailingAttempt)
class MailingAttemptAdmin(admin.ModelAdmin):
    list_display = ('mailing', 'recipient', 'status', 'attempt_time', 'short_response')
    list_filter = ('status', 'attempt_time', 'mailing__owner')
    search_fields = ('mailing__message__subject', 'recipient__email', 'server_response')
    list_per_page = 30
    date_hierarchy = 'attempt_time'

    readonly_fields = ('mailing', 'recipient', 'status', 'attempt_time', 'server_response')

    def short_response(self, obj):
        return obj.server_response[:50] + '...' if len(obj.server_response) > 50 else obj.server_response

    short_response.short_description = 'Ответ сервера'

    def has_add_permission(self, request):
        return False  # Запрещаем создавать вручную

    def has_change_permission(self, request, obj=None):
        return False  # Запрещаем редактировать
