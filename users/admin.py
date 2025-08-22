from django.contrib import admin
from django.contrib.admin import AdminSite
from django.utils.html import format_html
from django.contrib.admin.templatetags.admin_list import pagination
from django.utils.safestring import mark_safe
from .models import CustomUser, UserLog, QuickAction

class CihazTakipAdminSite(AdminSite):
    """Özelleştirilmiş Django Admin sitesi"""
    site_header = "🚀 Cihaz Takip Sistemi Yönetimi"
    site_title = "Cihaz Takip Admin"
    index_title = "🎛️ Sistem Yönetimi Paneli"
    
    def get_app_list(self, request):
        """Uygulama listesini özelleştir"""
        app_list = super().get_app_list(request)
        
        # Uygulama isimlerini Türkçeleştir
        app_dict = {
            'users': '👥 Kullanıcı Yönetimi',
            'devices': '📱 Cihaz Yönetimi',
            'dashboard': '📊 Dashboard',
            'auth': '🔐 Kimlik Doğrulama',
            'sessions': '🔄 Oturum Yönetimi',
        }
        
        for app in app_list:
            if app['app_label'] in app_dict:
                app['name'] = app_dict[app['app_label']]
        
        return app_list

# Özel admin sitesi oluştur
admin_site = CihazTakipAdminSite(name='cihaz_takip_admin')

class CustomUserAdmin(admin.ModelAdmin):
    """Özelleştirilmiş kullanıcı admin paneli"""
    list_display = ['username', 'email', 'full_name', 'tc_kimlik', 'role', 'is_active', 'status_badge', 'created_date', 'profile_image_display']
    list_filter = ['role', 'is_active', 'is_staff', 'is_superuser', 'is_locked', 'date_joined']
    search_fields = ['username', 'email', 'first_name', 'last_name', 'tc_kimlik']
    list_editable = ['is_active', 'role']
    ordering = ['-date_joined']
    
    fieldsets = (
        ('👤 Temel Bilgiler', {
            'fields': ('username', 'email', 'first_name', 'last_name', 'tc_kimlik', 'phone')
        }),
        ('🖼️ Profil', {
            'fields': ('profile_image',)
        }),
        ('🔐 Güvenlik', {
            'fields': ('password',)
        }),
        ('👑 Yetkiler', {
            'fields': ('role', 'is_active', 'is_staff', 'is_superuser', 'is_locked')
        }),
        ('📅 Tarihler', {
            'fields': ('date_joined', 'last_login'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['date_joined', 'last_login']
    
    def full_name(self, obj):
        """Tam ad gösterimi"""
        if obj.first_name and obj.last_name:
            return f"{obj.first_name} {obj.last_name}"
        return obj.username
    full_name.short_description = '👤 Tam Ad'
    
    def status_badge(self, obj):
        """Durum badge'i"""
        if obj.is_locked:
            return format_html('<span class="px-2 py-1 text-xs rounded-full bg-red-900 text-red-300">🔒 Kilitli</span>')
        elif obj.is_active:
            return format_html('<span class="px-2 py-1 text-xs rounded-full bg-green-900 text-green-300">✅ Aktif</span>')
        else:
            return format_html('<span class="px-2 py-1 text-xs rounded-full bg-gray-900 text-gray-300">❌ Pasif</span>')
    status_badge.short_description = '📊 Durum'
    
    def created_date(self, obj):
        """Oluşturulma tarihi"""
        return obj.date_joined.strftime('%d.%m.%Y %H:%M')
    created_date.short_description = '📅 Kayıt Tarihi'
    
    def profile_image_display(self, obj):
        """Profil resmi gösterimi"""
        if obj.profile_image:
            return format_html('<img src="{}" style="width: 40px; height: 40px; border-radius: 50%; object-fit: cover;" />', obj.profile_image.url)
        return format_html('<div style="width: 40px; height: 40px; border-radius: 50%; background: linear-gradient(45deg, #06b6d4, #3b82f6); display: flex; align-items: center; justify-content: center; color: white; font-size: 16px;">👤</div>')
    profile_image_display.short_description = '🖼️ Profil'
    
    class Media:
        css = {
            'all': ('admin/css/custom_admin.css',)
        }

class UserLogAdmin(admin.ModelAdmin):
    """Kullanıcı log admin paneli"""
    list_display = ['user', 'log_type_badge', 'description_short', 'ip_address', 'created_at_formatted']
    list_filter = ['log_type', 'created_at', 'ip_address']
    search_fields = ['user__username', 'user__email', 'description', 'ip_address']
    ordering = ['-created_at']
    readonly_fields = ['user', 'log_type', 'description', 'ip_address', 'user_agent', 'created_at']
    
    fieldsets = (
        ('👤 Kullanıcı Bilgileri', {
            'fields': ('user', 'log_type')
        }),
        ('📝 Log Detayları', {
            'fields': ('description', 'ip_address', 'user_agent')
        }),
        ('📅 Zaman Bilgisi', {
            'fields': ('created_at',)
        }),
    )
    
    def log_type_badge(self, obj):
        """Log türü badge'i"""
        colors = {
            'login': 'bg-green-900 text-green-300',
            'logout': 'bg-blue-900 text-blue-300',
            'login_failed': 'bg-red-900 text-red-300',
            'password_change': 'bg-yellow-900 text-yellow-300',
            'profile_update': 'bg-purple-900 text-purple-300',
            'user_created': 'bg-green-900 text-green-300',
            'user_updated': 'bg-blue-900 text-blue-300',
            'user_deleted': 'bg-red-900 text-red-300',
            'device_add': 'bg-green-900 text-green-300',
            'device_edit': 'bg-yellow-900 text-yellow-300',
            'device_delete': 'bg-red-900 text-red-300',
            'permission_update': 'bg-purple-900 text-purple-300',
            'account_locked': 'bg-red-900 text-red-300',
            'account_unlocked': 'bg-green-900 text-green-300',
            'bulk_action': 'bg-indigo-900 text-indigo-300',
            'export_data': 'bg-teal-900 text-teal-300',
            'system_access': 'bg-gray-900 text-gray-300',
            'admin_action': 'bg-pink-900 text-pink-300',
        }
        
        color_class = colors.get(obj.log_type, 'bg-gray-900 text-gray-300')
        return format_html('<span class="px-2 py-1 text-xs rounded-full {}">{}</span>', 
                         color_class, obj.get_log_type_display())
    log_type_badge.short_description = '🏷️ Log Türü'
    
    def description_short(self, obj):
        """Kısa açıklama"""
        if len(obj.description) > 50:
            return obj.description[:50] + '...'
        return obj.description
    description_short.short_description = '📝 Açıklama'
    
    def created_at_formatted(self, obj):
        """Formatlanmış tarih"""
        return obj.created_at.strftime('%d.%m.%Y %H:%M:%S')
    created_at_formatted.short_description = '📅 Tarih'

class QuickActionAdmin(admin.ModelAdmin):
    """Hızlı İşlemler admin paneli"""
    list_display = ['user', 'action_badge', 'display_name', 'icon_display', 'color_badge', 'order', 'is_active', 'status_badge', 'created_at_formatted']
    list_filter = ['action', 'color', 'is_active', 'created_at']
    search_fields = ['user__username', 'user__email', 'display_name']
    list_editable = ['order', 'is_active']
    ordering = ['user', 'order']
    
    fieldsets = (
        ('👤 Kullanıcı Bilgileri', {
            'fields': ('user', 'action')
        }),
        ('🎨 Görünüm Ayarları', {
            'fields': ('display_name', 'icon', 'color', 'order')
        }),
        ('📊 Durum', {
            'fields': ('is_active',)
        }),
    )
    
    def action_badge(self, obj):
        """İşlem badge'i"""
        colors = {
            'device_add': 'bg-green-900 text-green-300',
            'device_list': 'bg-blue-900 text-blue-300',
            'user_add': 'bg-purple-900 text-purple-300',
            'user_list': 'bg-indigo-900 text-indigo-300',
            'statistics': 'bg-yellow-900 text-yellow-300',
            'activity_log': 'bg-teal-900 text-teal-300',
            'system_info': 'bg-gray-900 text-gray-300',
            'admin_panel': 'bg-pink-900 text-pink-300',
            'profile': 'bg-cyan-900 text-cyan-300',
            'change_password': 'bg-orange-900 text-orange-300',
            'export_csv': 'bg-green-900 text-green-300',
            'export_json': 'bg-blue-900 text-blue-300',
            'bulk_actions': 'bg-purple-900 text-purple-300',
            'permissions': 'bg-red-900 text-red-300',
        }
        
        color_class = colors.get(obj.action, 'bg-gray-900 text-gray-300')
        return format_html('<span class="px-2 py-1 text-xs rounded-full {}">{}</span>', 
                         color_class, obj.get_action_display())
    action_badge.short_description = '⚡ İşlem'
    
    def icon_display(self, obj):
        """İkon gösterimi"""
        return format_html('<i class="{} text-lg"></i>', obj.icon)
    icon_display.short_description = '🎯 İkon'
    
    def color_badge(self, obj):
        """Renk badge'i"""
        color_map = {
            'cyan': 'bg-cyan-600',
            'blue': 'bg-blue-600',
            'green': 'bg-green-600',
            'yellow': 'bg-yellow-600',
            'red': 'bg-red-600',
            'purple': 'bg-purple-600',
            'pink': 'bg-pink-600',
            'indigo': 'bg-indigo-600',
        }
        
        color_class = color_map.get(obj.color, 'bg-gray-600')
        return format_html('<div class="w-4 h-4 rounded-full {}"></div>', color_class)
    color_badge.short_description = '🎨 Renk'
    
    def status_badge(self, obj):
        """Durum badge'i"""
        if obj.is_active:
            return format_html('<span class="px-2 py-1 text-xs rounded-full bg-green-900 text-green-300">✅ Aktif</span>')
        else:
            return format_html('<span class="px-2 py-1 text-xs rounded-full bg-red-900 text-red-300">❌ Pasif</span>')
    status_badge.short_description = '📊 Durum'
    
    def created_at_formatted(self, obj):
        """Formatlanmış tarih"""
        return obj.created_at.strftime('%d.%m.%Y %H:%M')
    created_at_formatted.short_description = '📅 Oluşturulma'

# Admin panellerini kaydet
admin_site.register(CustomUser, CustomUserAdmin)
admin_site.register(UserLog, UserLogAdmin)
admin_site.register(QuickAction, QuickActionAdmin)

# Varsayılan admin sitesini değiştir
admin.site = admin_site
admin.autodiscover()
