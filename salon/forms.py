from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, Tattoo, Appointment, Review, TattooStyle, Lead, CareProduct


class CustomUserCreationForm(UserCreationForm):
    """Форма регистрации пользователя"""
    username = forms.CharField(max_length=150, required=True, label='Логин')
    first_name = forms.CharField(max_length=150, required=True, label='Имя')
    last_name = forms.CharField(max_length=150, required=True, label='Фамилия')
    phone = forms.CharField(max_length=20, required=True, label='Телефон')
    email = forms.EmailField(required=False, label='Email (необязательно)')
    
    class Meta:
        model = User
        fields = (
            'username',
            'first_name',
            'last_name',
            'phone',
            'email',
            'password1',
            'password2',
        )


class TattooForm(forms.ModelForm):
    """Форма для создания/редактирования татуировки"""
    class Meta:
        model = Tattoo
        fields = ['title', 'description', 'style', 'master', 'price', 'image', 'is_active']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'style': forms.Select(attrs={'class': 'form-control'}),
            'master': forms.Select(attrs={'class': 'form-control'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['master'].queryset = User.objects.filter(role='master')
        self.fields['style'].empty_label = 'Не выбрано (опционально)'
        self.fields['style'].required = False


class AppointmentAdminForm(forms.ModelForm):
    """Форма для админа: со статусом"""
    class Meta:
        model = Appointment
        fields = ['master', 'tattoo', 'date', 'time', 'status', 'notes']
        widgets = {
            'master': forms.Select(attrs={'class': 'form-control'}),
            'tattoo': forms.Select(attrs={'class': 'form-control'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['master'].queryset = User.objects.filter(role='master')
        self.fields['tattoo'].queryset = Tattoo.objects.filter(is_active=True)
        self.fields['tattoo'].required = False

class AppointmentForm(forms.ModelForm):
    """Форма для записи на сеанс"""
    class Meta:
        model = Appointment
        fields = ['master', 'tattoo', 'date', 'time', 'notes']
        widgets = {
            'master': forms.Select(attrs={'class': 'form-control', 'id': 'id_master'}),
            'tattoo': forms.Select(attrs={'class': 'form-control'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date', 'id': 'id_date'}),
            'time': forms.Select(attrs={'class': 'form-control', 'id': 'id_time'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['master'].queryset = User.objects.filter(role='master')
        self.fields['master'].empty_label = 'Выберите мастера'
        self.fields['tattoo'].queryset = Tattoo.objects.filter(is_active=True)
        self.fields['tattoo'].empty_label = 'Не выбрано (опционально)'
        self.fields['tattoo'].required = False
        
        # Инициализируем поле времени как Select с пустым списком
        # Список будет заполнен через JavaScript
        self.fields['time'].widget = forms.Select(
            choices=[('', 'Сначала выберите мастера и дату')],
            attrs={'class': 'form-control', 'id': 'id_time'}
        )


class ReviewForm(forms.ModelForm):
    """Форма для отзыва"""
    class Meta:
        model = Review
        fields = ['master', 'tattoo', 'rating', 'text']
        widgets = {
            'master': forms.Select(attrs={'class': 'form-control'}),
            'tattoo': forms.Select(attrs={'class': 'form-control'}),
            'rating': forms.Select(attrs={'class': 'form-control'}),
            'text': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['master'].queryset = User.objects.filter(role='master')
        self.fields['master'].empty_label = 'Не выбрано (опционально)'
        self.fields['master'].required = False
        self.fields['tattoo'].queryset = Tattoo.objects.filter(is_active=True)
        self.fields['tattoo'].empty_label = 'Не выбрано (опционально)'
        self.fields['tattoo'].required = False


class UserForm(forms.ModelForm):
    """Форма для редактирования пользователя"""
    class Meta:
        model = User
        fields = ['username', 'email', 'phone', 'role', 'avatar']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'role': forms.Select(attrs={'class': 'form-control'}),
            'avatar': forms.FileInput(attrs={'class': 'form-control'}),
        }


class LeadForm(forms.ModelForm):
    """Форма для заявок (консультация, звонок, запись)"""
    class Meta:
        model = Lead
        fields = ['name', 'phone', 'email', 'lead_type', 'preferred_master', 'comment']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ваше имя'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+7 (___) ___-__-__'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'email@example.com'}),
            'lead_type': forms.Select(attrs={'class': 'form-control'}),
            'preferred_master': forms.Select(attrs={'class': 'form-control'}),
            'comment': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Комментарий / идея'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['preferred_master'].queryset = User.objects.filter(role='master')
        self.fields['preferred_master'].empty_label = 'Любой мастер'
        self.fields['email'].required = False


class CareProductForm(forms.ModelForm):
    """Форма для управления товарами ухода"""
    class Meta:
        model = CareProduct
        fields = ['title', 'price', 'description', 'image', 'is_active', 'sort_order']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'sort_order': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
        }

