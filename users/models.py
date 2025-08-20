from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _

class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('superadmin', 'Süper Admin'),
        ('admin', 'Admin'),
        ('user', 'Standart Kullanıcı'),
    ]
    
    # TC Kimlik Numarası - 11 haneli, sadece rakam
    tc_kimlik = models.CharField(
        max_length=11,
        unique=True,
        validators=[
            RegexValidator(
                regex=r'^[0-9]{11}$',
                message='TC Kimlik Numarası 11 haneli olmalıdır ve sadece rakam içermelidir.'
            )
        ],
        verbose_name='TC Kimlik Numarası',
        help_text='11 haneli TC Kimlik Numarası'
    )
    
    # Kullanıcı rolü
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='user',
        verbose_name='Kullanıcı Rolü'
    )
    
    # Kullanıcı telefon numarası
    phone = models.CharField(
        max_length=15,
        blank=True,
        null=True,
        verbose_name='Telefon Numarası'
    )
    
    # Kullanıcı adı ve soyadı
    first_name = models.CharField(
        max_length=150,
        verbose_name='Ad'
    )
    
    last_name = models.CharField(
        max_length=150,
        verbose_name='Soyad'
    )
    
    # Email zorunlu
    email = models.EmailField(
        unique=True,
        verbose_name='E-posta Adresi'
    )
    
    # Hesap aktif mi?
    is_active = models.BooleanField(
        default=True,
        verbose_name='Hesap Aktif'
    )
    
    # Son giriş tarihi
    last_login = models.DateTimeField(
        auto_now=True,
        verbose_name='Son Giriş'
    )
    
    # Kayıt tarihi
    date_joined = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Kayıt Tarihi'
    )
    
    # Hatalı giriş sayısı
    failed_login_attempts = models.PositiveIntegerField(
        default=0,
        verbose_name='Başarısız Giriş Denemeleri'
    )
    
    # Hesap kilitli mi?
    is_locked = models.BooleanField(
        default=False,
        verbose_name='Hesap Kilitli'
    )
    
    # Hesap kilitlenme tarihi
    locked_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='Kilitlenme Tarihi'
    )
    
    # Profil resmi
    profile_image = models.ImageField(
        upload_to='profile_images/',
        blank=True,
        null=True,
        verbose_name='Profil Resmi'
    )
    
    class Meta:
        verbose_name = 'Kullanıcı'
        verbose_name_plural = 'Kullanıcılar'
        ordering = ['-date_joined']
        db_table = 'kullanicilar'
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.tc_kimlik})"
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    def get_short_name(self):
        return self.first_name
    
    def is_admin(self):
        return self.role in ['admin', 'superadmin']
    
    def is_superadmin(self):
        return self.role == 'superadmin'
    
    def can_manage_users(self):
        return self.role in ['admin', 'superadmin']
    
    def can_manage_devices(self):
        return True  # Tüm kullanıcılar cihaz yönetebilir
    
    def can_view_all_devices(self):
        return self.role in ['admin', 'superadmin']
    
    def increment_failed_login(self):
        """Başarısız giriş denemesini artırır"""
        self.failed_login_attempts += 1
        if self.failed_login_attempts >= 5:
            self.is_locked = True
            from django.utils import timezone
            self.locked_at = timezone.now()
        self.save()
    
    def reset_failed_login(self):
        """Başarısız giriş denemelerini sıfırlar"""
        self.failed_login_attempts = 0
        self.is_locked = False
        self.locked_at = None
        self.save()
    
    def unlock_account(self):
        """Hesabı açar"""
        self.is_locked = False
        self.failed_login_attempts = 0
        self.locked_at = None
        self.save()


class UserLog(models.Model):
    """Kullanıcı aktivite logları"""
    
    LOG_TYPE_CHOICES = [
        ('login', 'Giriş'),
        ('logout', 'Çıkış'),
        ('login_failed', 'Başarısız Giriş'),
        ('password_change', 'Şifre Değişikliği'),
        ('profile_update', 'Profil Güncelleme'),
        ('device_add', 'Cihaz Ekleme'),
        ('device_update', 'Cihaz Güncelleme'),
        ('device_delete', 'Cihaz Silme'),
        ('account_locked', 'Hesap Kilitlendi'),
        ('account_unlocked', 'Hesap Açıldı'),
    ]
    
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='logs',
        verbose_name='Kullanıcı'
    )
    
    log_type = models.CharField(
        max_length=20,
        choices=LOG_TYPE_CHOICES,
        verbose_name='Log Türü'
    )
    
    description = models.TextField(
        verbose_name='Açıklama'
    )
    
    ip_address = models.GenericIPAddressField(
        blank=True,
        null=True,
        verbose_name='IP Adresi'
    )
    
    user_agent = models.TextField(
        blank=True,
        null=True,
        verbose_name='Tarayıcı Bilgisi'
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Oluşturulma Tarihi'
    )
    
    class Meta:
        verbose_name = 'Kullanıcı Logu'
        verbose_name_plural = 'Kullanıcı Logları'
        ordering = ['-created_at']
        db_table = 'kullanici_loglari'
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.get_log_type_display()} - {self.created_at}"
    
    @classmethod
    def log_activity(cls, user, log_type, description, ip_address=None, user_agent=None):
        """Kullanıcı aktivitesini loglar"""
        return cls.objects.create(
            user=user,
            log_type=log_type,
            description=description,
            ip_address=ip_address,
            user_agent=user_agent
        )
