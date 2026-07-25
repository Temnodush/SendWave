from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django import forms
from .models import CustomUser


class CustomUserCreationForm(UserCreationForm):
    phone_number = forms.CharField(max_length=15, required=False, help_text="Необязательное поле. Введите свой номер телефона.")
    username = forms.CharField(max_length=50, required=True)

    class Meta:
        model = CustomUser
        fields = ['email', 'username' ,'first_name','last_name','phone_number', 'avatar' , 'password1' , 'password2' ]

    def clean_phone_number(self):
        phone_number = self.cleaned_data.get('phone_number')
        if phone_number and not phone_number.isdigit():
            raise forms.ValidationError("Телефон должен состоять только из цифр")
        return phone_number

    def __init__(self, *args, **kwargs):
        super(CustomUserCreationForm, self).__init__(*args, **kwargs)

        # Общие настройки для всех полей
        for field_name, field in self.fields.items():
            if field.widget.__class__.__name__ == 'CheckboxInput':
                field.widget.attrs.update({'class': 'form-check-input'})
            elif field.widget.__class__.__name__ == 'Select':
                field.widget.attrs.update({'class': 'form-select rounded-3'})
            elif field.widget.__class__.__name__ == 'ClearableFileInput':
                field.widget.attrs.update({'class': 'form-control rounded-3'})
            else:
                field.widget.attrs.update({'class': 'form-control rounded-3'})

        # Кастомные placeholder и label
        self.fields['email'].widget.attrs['placeholder'] = 'Введите email'
        self.fields['email'].label = 'Электронная почта'

        self.fields['username'].widget.attrs['placeholder'] = 'Введите логин'
        self.fields['username'].label = 'Имя пользователя'

        self.fields['first_name'].widget.attrs['placeholder'] = 'Ваше имя'
        self.fields['first_name'].label = 'Имя'

        self.fields['last_name'].widget.attrs['placeholder'] = 'Ваша фамилия'
        self.fields['last_name'].label = 'Фамилия'


        self.fields['phone_number'].widget.attrs['placeholder'] = 'Номер телефона'
        self.fields['phone_number'].label = 'Телефон'

        self.fields['avatar'].label = 'Аватар'

        self.fields['password1'].widget.attrs['placeholder'] = 'Введите пароль'
        self.fields['password1'].label = 'Пароль'
        self.fields['password1'].help_text = 'Минимум 8 символов, не только цифры'

        self.fields['password2'].widget.attrs['placeholder'] = 'Подтвердите пароль'
        self.fields['password2'].label = 'Подтверждение пароля'
        self.fields['password2'].help_text = ''


class CustomAuthenticationForm(AuthenticationForm):
    """Стилизованная форма авторизации"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['username'].label = 'Электронная почта'
        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Введите email',
            'autofocus': True,
        })

        self.fields['password'].label = 'Пароль'
        self.fields['password'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Введите пароль',
        })

class CustomUserChangeForm(forms.ModelForm):
    """Форма для редактирования профиля (без пароля)"""

    class Meta:
        model = CustomUser
        fields = ['username', 'first_name', 'last_name', 'phone_number', 'avatar']
        # email не включаем, так как его обычно не меняют

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Применяем те же классы, что и в CustomUserCreationForm
        for field_name, field in self.fields.items():
            if field.widget.__class__.__name__ == 'CheckboxInput':
                field.widget.attrs.update({'class': 'form-check-input'})
            elif field.widget.__class__.__name__ == 'Select':
                field.widget.attrs.update({'class': 'form-select rounded-3'})
            elif field.widget.__class__.__name__ == 'ClearableFileInput':
                field.widget.attrs.update({'class': 'form-control rounded-3'})
            else:
                field.widget.attrs.update({'class': 'form-control rounded-3'})

        # Кастомные placeholder и label
        self.fields['username'].widget.attrs['placeholder'] = 'Введите логин'
        self.fields['username'].label = 'Имя пользователя'

        self.fields['first_name'].widget.attrs['placeholder'] = 'Ваше имя'
        self.fields['first_name'].label = 'Имя'

        self.fields['last_name'].widget.attrs['placeholder'] = 'Ваша фамилия'
        self.fields['last_name'].label = 'Фамилия'

        self.fields['phone_number'].widget.attrs['placeholder'] = 'Номер телефона'
        self.fields['phone_number'].label = 'Телефон'

        self.fields['avatar'].label = 'Аватар'