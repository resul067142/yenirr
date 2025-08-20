from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _
from .models import CustomUser

class CustomUserCreationForm(UserCreationForm):
    """Kullanıcı kayıt formu"""
    
    tc_kimlik = forms.CharField(
        max_length=11,
        validators=[
            RegexValidator(
                regex=r'^[0-9]{11}$',
                message='TC Kimlik Numarası 11 haneli olmalıdır ve sadece rakam içermelidir.'
            )
        ],
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'TC Kimlik Numarası'
        }),
        label='TC Kimlik Numarası',
        help_text='11 haneli TC Kimlik Numarası'
    )
    
    first_name = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'Ad'
        }),
        label='Ad'
    )
    
    last_name = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'Soyad'
        }),
        label='Soyad'
    )
    
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'E-posta Adresi'
        }),
        label='E-posta Adresi'
    )
    
    phone = forms.CharField(
        max_length=15,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'Telefon Numarası (Opsiyonel)'
        }),
        label='Telefon Numarası'
    )
    
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'Kullanıcı Adı'
        }),
        label='Kullanıcı Adı'
    )
    
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'Şifre'
        }),
        label='Şifre'
    )
    
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'Şifre Tekrarı'
        }),
        label='Şifre Tekrarı'
    )
    
    class Meta:
        model = CustomUser
        fields = ('tc_kimlik', 'username', 'first_name', 'last_name', 'email', 'phone', 'password1', 'password2')
    
    def clean_tc_kimlik(self):
        tc_kimlik = self.cleaned_data.get('tc_kimlik')
        if CustomUser.objects.filter(tc_kimlik=tc_kimlik).exists():
            raise forms.ValidationError('Bu TC Kimlik Numarası zaten kayıtlı.')
        return tc_kimlik
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if CustomUser.objects.filter(email=email).exists():
            raise forms.ValidationError('Bu e-posta adresi zaten kayıtlı.')
        return email
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if CustomUser.objects.filter(username=username).exists():
            raise forms.ValidationError('Bu kullanıcı adı zaten kullanılıyor.')
        return username


class CustomAuthenticationForm(AuthenticationForm):
    """Kullanıcı giriş formu"""
    
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'TC Kimlik Numarası veya Kullanıcı Adı'
        }),
        label='TC Kimlik Numarası veya Kullanıcı Adı'
    )
    
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'Şifre'
        }),
        label='Şifre'
    )
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        # TC Kimlik Numarası veya kullanıcı adı olabilir
        if username.isdigit() and len(username) == 11:
            # TC Kimlik Numarası girilmiş, kullanıcıyı bul
            try:
                user = CustomUser.objects.get(tc_kimlik=username)
                return user.username
            except CustomUser.DoesNotExist:
                raise forms.ValidationError('Bu TC Kimlik Numarası ile kayıtlı kullanıcı bulunamadı.')
        return username


class CustomUserUpdateForm(forms.ModelForm):
    """Kullanıcı profil güncelleme formu"""
    
    first_name = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
        }),
        label='Ad'
    )
    
    last_name = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
        }),
        label='Soyad'
    )
    
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
        }),
        label='E-posta Adresi'
    )
    
    phone = forms.CharField(
        max_length=15,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
        }),
        label='Telefon Numarası'
    )
    
    class Meta:
        model = CustomUser
        fields = ('first_name', 'last_name', 'email', 'phone')
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if CustomUser.objects.exclude(pk=self.instance.pk).filter(email=email).exists():
            raise forms.ValidationError('Bu e-posta adresi zaten kullanılıyor.')
        return email


class PasswordChangeForm(forms.Form):
    """Şifre değiştirme formu"""
    
    old_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'Mevcut Şifre'
        }),
        label='Mevcut Şifre'
    )
    
    new_password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'Yeni Şifre'
        }),
        label='Yeni Şifre'
    )
    
    new_password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'Yeni Şifre Tekrarı'
        }),
        label='Yeni Şifre Tekrarı'
    )
    
    def clean(self):
        cleaned_data = super().clean()
        new_password1 = cleaned_data.get('new_password1')
        new_password2 = cleaned_data.get('new_password2')
        
        if new_password1 and new_password2:
            if new_password1 != new_password2:
                raise forms.ValidationError('Yeni şifreler eşleşmiyor.')
        
        return cleaned_data
