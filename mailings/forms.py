from django import forms
from django.utils import timezone
from django.core.exceptions import ValidationError

from .models import EmailRecipient, Message, Mailing


class ClientForm(forms.ModelForm):
    class Meta:
        model = EmailRecipient
        fields = ['email', 'fullname', 'comment']
        widgets = {
            'comment': forms.Textarea(attrs={'rows': 3}),
        }


class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['subject', 'body']
        widgets = {
            'body': forms.Textarea(attrs={'rows': 10}),
        }


class MailingForm(forms.ModelForm):
    # Для ежедневной — множественный выбор
    weekdays_multiple = forms.MultipleChoiceField(
        choices=Mailing.WEEKDAY_CHOICES,
        widget=forms.CheckboxSelectMultiple(),
        required=False,
        label="Дни отправки"
    )

    # Для еженедельной — один день
    weekday_single = forms.ChoiceField(
        choices=[('', 'Выберите день...')] + list(Mailing.WEEKDAY_CHOICES),
        required=False,
        label="День недели"
    )

    class Meta:
        model = Mailing
        fields = [
            'start_time', 'end_time', 'message', 'recipients',
            'period', 'send_time', 'day_of_month'
        ]
        widgets = {
            'start_time': forms.DateTimeInput(
                attrs={'type': 'datetime-local'},
                format='%Y-%m-%dT%H:%M'
            ),
            'end_time': forms.DateTimeInput(
                attrs={'type': 'datetime-local'},
                format='%Y-%m-%dT%H:%M'
            ),
            'send_time': forms.TimeInput(
                attrs={'type': 'time'},
                format='%H:%M'
            ),
            'recipients': forms.CheckboxSelectMultiple(),
            'day_of_month': forms.NumberInput(
                attrs={'min': 1, 'max': 31, 'placeholder': '1-31'}
            ),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)

        if user:
            self.fields['message'].queryset = Message.objects.filter(owner=user)
            self.fields['recipients'].queryset = EmailRecipient.objects.filter(owner=user)

        # Загружаем weekdays при редактировании
        if self.instance and self.instance.pk and self.instance.weekdays:
            if self.instance.period == Mailing.PERIOD_DAILY:
                self.initial['weekdays_multiple'] = self.instance.weekdays
            elif self.instance.period == Mailing.PERIOD_WEEKLY:
                if len(self.instance.weekdays) > 0:
                    self.initial['weekday_single'] = self.instance.weekdays[0]

    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        period = cleaned_data.get('period')
        send_time = cleaned_data.get('send_time')
        weekdays_multiple = cleaned_data.get('weekdays_multiple', [])
        weekday_single = cleaned_data.get('weekday_single')
        day_of_month = cleaned_data.get('day_of_month')

        # Валидация дат
        if start_time and end_time:
            if start_time >= end_time:
                raise ValidationError('Дата начала должна быть раньше даты окончания')

            if not self.instance.pk and start_time < timezone.now():
                raise ValidationError('Дата начала не может быть в прошлом')

        # Валидация по типу рассылки
        if period == Mailing.PERIOD_ONCE:
            # Для разовой — время отправки опционально
            pass

        elif period == Mailing.PERIOD_DAILY:
            if not send_time:
                self.add_error('send_time', 'Укажите время отправки')
            # Дни недели опциональны — если не выбраны, будет каждый день

        elif period == Mailing.PERIOD_WEEKLY:
            if not send_time:
                self.add_error('send_time', 'Укажите время отправки')
            if not weekday_single:
                self.add_error('weekday_single', 'Выберите день недели')

        elif period == Mailing.PERIOD_MONTHLY:
            if not send_time:
                self.add_error('send_time', 'Укажите время отправки')
            if not day_of_month or not (1 <= day_of_month <= 31):
                self.add_error('day_of_month', 'Укажите день месяца (1-31)')

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)

        period = self.cleaned_data.get('period')

        # Устанавливаем weekdays в зависимости от типа рассылки
        if period == Mailing.PERIOD_ONCE:
            instance.weekdays = []
            instance.day_of_month = None

        elif period == Mailing.PERIOD_DAILY:
            weekdays = self.cleaned_data.get('weekdays_multiple', [])
            if weekdays:
                instance.weekdays = [int(d) for d in weekdays]
            else:
                # Все дни по умолчанию
                instance.weekdays = [0, 1, 2, 3, 4, 5, 6]
            instance.day_of_month = None

        elif period == Mailing.PERIOD_WEEKLY:
            weekday = self.cleaned_data.get('weekday_single')
            if weekday:
                instance.weekdays = [int(weekday)]
            instance.day_of_month = None

        elif period == Mailing.PERIOD_MONTHLY:
            instance.weekdays = []
            # day_of_month уже установлен из формы

        if commit:
            instance.save()
            self.save_m2m()

        return instance
