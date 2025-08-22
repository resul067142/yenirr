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
    
    @property
    def is_superadmin(self):
        """Kullanıcı süper admin mi?"""
        return self.role == 'superadmin'
    
    @property
    def can_manage_users(self):
        """Kullanıcı kullanıcı yönetimi yapabilir mi?"""
        return self.role in ['admin', 'superadmin']
    
    @property
    def can_manage_devices(self):
        """Kullanıcı cihaz yönetimi yapabilir mi?"""
        return self.role in ['admin', 'superadmin']
    
    @property
    def can_view_all_devices(self):
        """Kullanıcı tüm cihazları görebilir mi?"""
        return self.role in ['admin', 'superadmin']
    
    @property
    def can_export_data(self):
        """Kullanıcı veri dışa aktarabilir mi?"""
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
        ('login', 'Giriş Yapıldı'),
        ('logout', 'Çıkış Yapıldı'),
        ('login_failed', 'Başarısız Giriş'),
        ('password_change', 'Şifre Değiştirildi'),
        ('profile_update', 'Profil Güncellendi'),
        ('user_created', 'Kullanıcı Oluşturuldu'),
        ('user_updated', 'Kullanıcı Güncellendi'),
        ('user_deleted', 'Kullanıcı Silindi'),
        ('device_add', 'Cihaz Eklendi'),
        ('device_edit', 'Cihaz Düzenlendi'),
        ('device_delete', 'Cihaz Silindi'),
        ('permission_update', 'Yetki Güncellendi'),
        ('account_locked', 'Hesap Kilitlendi'),
        ('account_unlocked', 'Hesap Açıldı'),
        ('bulk_action', 'Toplu İşlem'),
        ('export_data', 'Veri Dışa Aktarıldı'),
        ('system_access', 'Sistem Erişimi'),
        ('admin_action', 'Admin İşlemi'),
    ]
    
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, verbose_name='Kullanıcı')
    log_type = models.CharField(max_length=50, choices=LOG_TYPE_CHOICES, verbose_name='Log Türü')
    description = models.TextField(verbose_name='Açıklama')
    ip_address = models.GenericIPAddressField(blank=True, null=True, verbose_name='IP Adresi')
    user_agent = models.TextField(blank=True, null=True, verbose_name='User Agent')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Oluşturulma Tarihi')
    
    class Meta:
        verbose_name = 'Kullanıcı Logu'
        verbose_name_plural = 'Kullanıcı Logları'
        ordering = ['-created_at']
        db_table = 'kullanici_loglari'
    
    def __str__(self):
        return f"{self.user.username} - {self.get_log_type_display()} - {self.created_at}"
    
    @classmethod
    def log_activity(cls, user, log_type, description, ip_address=None, user_agent=None):
        """Aktivite logu oluştur"""
        return cls.objects.create(
            user=user,
            log_type=log_type,
            description=description,
            ip_address=ip_address,
            user_agent=user_agent
        )


class QuickAction(models.Model):
    """Kullanıcı hızlı işlemleri"""
    ACTION_CHOICES = [
        ('device_add', 'Cihaz Ekle'),
        ('device_list', 'Cihaz Listesi'),
        ('user_add', 'Kullanıcı Ekle'),
        ('user_list', 'Kullanıcı Listesi'),
        ('statistics', 'İstatistikler'),
        ('activity_log', 'Aktivite Logları'),
        ('system_info', 'Sistem Bilgileri'),
        ('admin_panel', 'Yönetim Paneli'),
        ('profile', 'Profil'),
        ('change_password', 'Şifre Değiştir'),
        ('export_csv', 'CSV Export'),
        ('export_json', 'JSON Export'),
        ('bulk_actions', 'Toplu İşlemler'),
        ('permissions', 'Yetki Yönetimi'),
    ]
    
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, verbose_name='Kullanıcı')
    action = models.CharField(max_length=50, choices=ACTION_CHOICES, verbose_name='İşlem')
    display_name = models.CharField(max_length=100, verbose_name='Görünen Ad')
    icon = models.CharField(max_length=50, default='fas fa-star', verbose_name='İkon')
    color = models.CharField(max_length=20, default='cyan', verbose_name='Renk')
    order = models.PositiveIntegerField(default=0, verbose_name='Sıra')
    is_active = models.BooleanField(default=True, verbose_name='Aktif')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Oluşturulma Tarihi')
    
    class Meta:
        verbose_name = 'Hızlı İşlem'
        verbose_name_plural = 'Hızlı İşlemler'
        ordering = ['order', 'created_at']
        unique_together = ['user', 'action']
        db_table = 'hizli_islemler'
    
    def __str__(self):
        return f"{self.user.username} - {self.get_action_display()}"
    
    def get_url(self):
        """İşlem URL'ini döndür"""
        url_mapping = {
            'device_add': '/devices/add/',
            'device_list': '/devices/',
            'user_add': '/users/add/',
            'user_list': '/users/list/',
            'statistics': '/statistics/',
            'activity_log': '/activity-log/',
            'system_info': '/system-info/',
            'admin_panel': '/admin-panel/',
            'profile': '/users/profile/',
            'change_password': '/users/change-password/',
            'export_csv': '/devices/export/csv/',
            'export_json': '/devices/export/json/',
            'bulk_actions': '/users/permissions/',
            'permissions': '/users/permissions/',
        }
        return url_mapping.get(self.action, '#')
    
    def get_color_classes(self):
        """Renk CSS sınıflarını döndür"""
        color_mapping = {
            'cyan': 'bg-cyan-600 hover:bg-cyan-700 text-white',
            'blue': 'bg-blue-600 hover:bg-blue-700 text-white',
            'green': 'bg-green-600 hover:bg-green-700 text-white',
            'yellow': 'bg-yellow-600 hover:bg-yellow-700 text-white',
            'red': 'bg-red-600 hover:bg-red-700 text-white',
            'purple': 'bg-purple-600 hover:bg-purple-700 text-white',
            'pink': 'bg-pink-600 hover:bg-pink-700 text-white',
            'indigo': 'bg-indigo-600 hover:bg-indigo-700 text-white',
        }
        return color_mapping.get(self.color, 'bg-cyan-600 hover:bg-cyan-700 text-white')
