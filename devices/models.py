from django.db import models
from django.conf import settings
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _

class Device(models.Model):
    DEVICE_TYPE_CHOICES = [
        ('phone', 'Telefon'),
        ('tablet', 'Tablet'),
        ('computer', 'Bilgisayar'),
        ('iot', 'IoT Cihazı'),
        ('vehicle_camera', 'Araç Kamerası'),
        ('vehicle_tracker', 'Araç Takip Cihazı'),
        ('ip_camera', 'IP Kamera'),
        ('other', 'Diğer'),
    ]
    
    # Cihaz sahibi (kullanıcı)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='devices',
        verbose_name='Cihaz Sahibi'
    )
    
    # GSM Numarası (zorunlu)
    gsm_number = models.CharField(
        max_length=15,
        validators=[
            RegexValidator(
                regex=r'^\+?[0-9]{10,15}$',
                message='Geçerli bir telefon numarası giriniz.'
            )
        ],
        verbose_name='GSM Numarası',
        help_text='Örnek: +905551234567 veya 05551234567'
    )
    
    # Cihaz E-mail Adresi (zorunlu, unique)
    device_email = models.EmailField(
        unique=True,
        verbose_name='Cihaz E-posta Adresi',
        help_text='Cihaza özel e-posta adresi'
    )
    
    # Cihaz E-mail No (opsiyonel, 15 haneli)
    email_number = models.CharField(
        max_length=15,
        blank=True,
        null=True,
        verbose_name='Cihaz E-mail No',
        help_text='15 haneli cihaz e-mail numarası'
    )
    
    # Cihaz Cinsi
    device_type = models.CharField(
        max_length=20,
        choices=DEVICE_TYPE_CHOICES,
        default='phone',
        verbose_name='Cihaz Cinsi'
    )
    
    # Cihaz Adı (opsiyonel)
    device_name = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='Cihaz Adı',
        help_text='Cihaza özel isim (örn: İş Telefonu)'
    )
    
    # Cihaz Markası (opsiyonel)
    brand = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name='Marka'
    )
    
    # Cihaz Modeli (opsiyonel)
    model = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name='Model'
    )
    
    # IMEI Numarası (opsiyonel)
    imei = models.CharField(
        max_length=15,
        blank=True,
        null=True,
        verbose_name='IMEI Numarası',
        help_text='15 haneli IMEI numarası'
    )
    
    # Cihaz Durumu
    is_active = models.BooleanField(
        default=True,
        verbose_name='Cihaz Aktif'
    )
    
    # Kayıt Tarihi (otomatik)
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Kayıt Tarihi'
    )
    
    # Güncelleme Tarihi
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Güncelleme Tarihi'
    )
    
    # Notlar (opsiyonel)
    notes = models.TextField(
        blank=True,
        null=True,
        verbose_name='Notlar',
        help_text='Cihaz hakkında ek bilgiler'
    )
    
    # Cihaz Birliği (opsiyonel)
    device_group = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='Cihaz Birliği',
        help_text='Cihazın ait olduğu grup veya birim'
    )
    
    class Meta:
        verbose_name = 'Cihaz'
        verbose_name_plural = 'Cihazlar'
        ordering = ['-created_at']
        db_table = 'cihazlar'
        unique_together = ['user', 'gsm_number']  # Bir kullanıcının aynı GSM numarasına sahip birden fazla cihazı olamaz
    
    def __str__(self):
        device_name = self.device_name or f"{self.get_device_type_display()}"
        return f"{device_name} - {self.gsm_number} ({self.user.get_full_name()})"
    
    def get_device_type_display_tr(self):
        """Cihaz cinsini Türkçe olarak döndürür"""
        return dict(self.DEVICE_TYPE_CHOICES).get(self.device_type, 'Bilinmeyen')
    
    def get_short_info(self):
        """Cihaz hakkında kısa bilgi döndürür"""
        return f"{self.get_device_type_display_tr()} - {self.gsm_number}"
    
    def is_phone(self):
        """Cihaz telefon mu?"""
        return self.device_type == 'phone'
    
    def is_tablet(self):
        """Cihaz tablet mi?"""
        return self.device_type == 'tablet'
    
    def is_computer(self):
        """Cihaz bilgisayar mı?"""
        return self.device_type == 'computer'
    
    def is_iot(self):
        """Cihaz IoT cihazı mı?"""
        return self.device_type == 'iot'
    
    def get_user_full_name(self):
        """Cihaz sahibinin tam adını döndürür"""
        return self.user.get_full_name()
    
    def get_user_tc(self):
        """Cihaz sahibinin TC kimlik numarasını döndürür"""
        return self.user.tc_kimlik
