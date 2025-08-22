from django.contrib import admin
from django.contrib.admin import AdminSite
from django.utils.html import format_html

class CihazTakipAdminSite(AdminSite):
    """Özelleştirilmiş Django Admin sitesi"""
    site_header = "Cihaz Takip Sistemi Yönetimi"
    site_title = "Cihaz Takip Admin"
    index_title = "Sistem Yönetimi Paneli"
    
    def get_app_list(self, request):
        """Uygulama listesini özelleştir"""
        app_list = super().get_app_list(request)
        
        # Uygulama isimlerini Türkçeleştir
        app_dict = {
            'users': 'Kullanıcı Yönetimi',
            'devices': 'Cihaz Yönetimi',
            'dashboard': 'Dashboard',
            'auth': 'Kimlik Doğrulama',
            'sessions': 'Oturum Yönetimi',
        }
        
        for app in app_list:
            if app['app_label'] in app_dict:
                app['name'] = app_dict[app['app_label']]
        
        return app_list

# Özel admin sitesi oluştur
admin_site = CihazTakipAdminSite(name='cihaz_takip_admin')

# Varsayılan admin sitesini değiştir
admin.site = admin_site
admin.autodiscover()
