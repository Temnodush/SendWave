from django import forms
from django.utils import timezone
from django.core.exceptions import ValidationError

from .models import EmailRecipient, Message, Mailing


class ClientForm(forms.ModelForm):
    """
    Форма создания/редактирования клиента.
    """

    class Meta:
        model = EmailRecipient
        fields = ['email', 'fullname', 'comment']
        widgets = {
            'comment': forms.Textarea(attrs={'rows': 3}),
        }


class MessageForm(forms.ModelForm):
    """
    Форма создания/редактирования сообщения.
    """

    class Meta:
        model = Message
        fields = ['subject', 'body']
        widgets = {
            'body': forms.Textarea(attrs={'rows': 10}),
        }


class MailingForm(forms.ModelForm):
    """
    Форма создания/редактирования рассылки.
    Фильтрует сообщения и получателей по текущему пользователю.
    """

    class Meta:
        model = Mailing
        fields = ['start_time', 'end_time', 'message', 'recipients']
        widgets = {
            'start_time': forms.DateTimeInput(
                attrs={'type': 'datetime-local'},
                format='%Y-%m-%dT%H:%M'
            ),
            'end_time': forms.DateTimeInput(
                attrs={'type': 'datetime-local'},
                format='%Y-%m-%dT%H:%M'
            ),
            'recipients': forms.CheckboxSelectMultiple(),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)

        if user:
            # Показываем только сообщения и клиентов текущего пользователя
            self.fields['message'].queryset = Message.objects.filter(owner=user)
            self.fields['recipients'].queryset = EmailRecipient.objects.filter(owner=user)

    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')

        if start_time and end_time:
            if start_time >= end_time:
                raise ValidationError('Дата начала должна быть раньше даты окончания')

            # Проверка на прошлое только при создании
            if not self.instance.pk and start_time < timezone.now():
                raise ValidationError('Дата начала не может быть в прошлом')

        return cleaned_data
