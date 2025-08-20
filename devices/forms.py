from django import forms
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _
from .models import Device

class DeviceForm(forms.ModelForm):
    """Cihaz ekleme/düzenleme formu"""
    
    device_name = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'Cihaz Adı (Opsiyonel)'
        }),
        label='Cihaz Adı',
        help_text='Cihaza özel isim (örn: İş Telefonu)'
    )
    
    gsm_number = forms.CharField(
        max_length=15,
        validators=[
            RegexValidator(
                regex=r'^\+?[0-9]{10,15}$',
                message='Geçerli bir telefon numarası giriniz.'
            )
        ],
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'GSM Numarası'
        }),
        label='GSM Numarası',
        help_text='Örnek: +905551234567 veya 05551234567'
    )
    
    device_email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'Cihaz E-posta Adresi'
        }),
        label='Cihaz E-posta Adresi',
        help_text='Cihaza özel e-posta adresi'
    )
    
    device_type = forms.ChoiceField(
        choices=Device.DEVICE_TYPE_CHOICES,
        widget=forms.Select(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
        }),
        label='Cihaz Cinsi'
    )
    
    brand = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'Marka (Opsiyonel)'
        }),
        label='Marka'
    )
    
    model = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'Model (Opsiyonel)'
        }),
        label='Model'
    )
    
    imei = forms.CharField(
        max_length=15,
        required=False,
        validators=[
            RegexValidator(
                regex=r'^[0-9]{15}$',
                message='IMEI numarası 15 haneli olmalıdır.'
            )
        ],
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'IMEI Numarası (Opsiyonel)'
        }),
        label='IMEI Numarası',
        help_text='15 haneli IMEI numarası'
    )
    
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
            'rows': 3,
            'placeholder': 'Cihaz hakkında ek bilgiler (Opsiyonel)'
        }),
        label='Notlar'
    )
    
    device_group = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'Cihaz Birliği (Opsiyonel)'
        }),
        label='Cihaz Birliği',
        help_text='Cihazın ait olduğu grup veya birim (örn: IT Departmanı)'
    )
    
    class Meta:
        model = Device
        fields = ['device_name', 'gsm_number', 'device_email', 'device_type', 'brand', 'model', 'imei', 'device_group', 'notes']
    
    def clean_device_email(self):
        email = self.cleaned_data.get('device_email')
        if self.instance.pk:  # Düzenleme
            if Device.objects.exclude(pk=self.instance.pk).filter(device_email=email).exists():
                raise forms.ValidationError('Bu e-posta adresi zaten kullanılıyor.')
        else:  # Yeni ekleme
            if Device.objects.filter(device_email=email).exists():
                raise forms.ValidationError('Bu e-posta adresi zaten kullanılıyor.')
        return email
    
    def clean_gsm_number(self):
        gsm = self.cleaned_data.get('gsm_number')
        # GSM numarasını formatla
        if gsm.startswith('0'):
            gsm = '+90' + gsm[1:]
        elif not gsm.startswith('+'):
            gsm = '+90' + gsm
        return gsm


class DeviceFilterForm(forms.Form):
    """Cihaz filtreleme formu"""
    
    device_type = forms.ChoiceField(
        choices=[('', 'Tüm Cihaz Türleri')] + Device.DEVICE_TYPE_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
        }),
        label='Cihaz Türü'
    )
    
    is_active = forms.ChoiceField(
        choices=[
            ('', 'Tüm Durumlar'),
            ('True', 'Aktif'),
            ('False', 'Pasif')
        ],
        required=False,
        widget=forms.Select(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
        }),
        label='Durum'
    )
    
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
            'type': 'date'
        }),
        label='Başlangıç Tarihi'
    )
    
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
            'type': 'date'
        }),
        label='Bitiş Tarihi'
    )
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'Cihaz adı, GSM, e-posta ara...'
        }),
        label='Arama'
    )
