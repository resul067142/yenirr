from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import Device

@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = ('device_name', 'device_type', 'gsm_number', 'device_email', 'user', 'is_active', 'created_at')
    list_filter = ('device_type', 'is_active', 'created_at', 'user__role')
    search_fields = ('device_name', 'gsm_number', 'device_email', 'user__username', 'user__tc_kimlik', 'user__first_name', 'user__last_name')
    ordering = ('-created_at',)
    
    fieldsets = (
        (_('Cihaz Bilgileri'), {
            'fields': ('device_name', 'device_type', 'gsm_number', 'device_email')
        }),
        (_('Teknik Detaylar'), {
            'fields': ('brand', 'model', 'imei')
        }),
        (_('Kullanıcı Bilgileri'), {
            'fields': ('user',)
        }),
        (_('Durum'), {
            'fields': ('is_active', 'notes')
        }),
        (_('Tarihler'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')
    
    def get_list_display(self, request):
        """Admin kullanıcısının rolüne göre list_display'i ayarlar"""
        if request.user.is_superuser or request.user.role in ['admin', 'superadmin']:
            return ('device_name', 'device_type', 'gsm_number', 'device_email', 'user', 'is_active', 'created_at')
        else:
            return ('device_name', 'device_type', 'gsm_number', 'device_email', 'is_active', 'created_at')
    
    def get_queryset(self, request):
        """Admin kullanıcısının rolüne göre queryset'i filtreler"""
        qs = super().get_queryset(request).select_related('user')
        if not request.user.is_superuser and request.user.role not in ['admin', 'superadmin']:
            qs = qs.filter(user=request.user)
        return qs
    
    def has_change_permission(self, request, obj=None):
        """Kullanıcının cihazı düzenleme yetkisi var mı?"""
        if obj is None:
            return True
        return request.user.is_superuser or request.user.role in ['admin', 'superadmin'] or obj.user == request.user
    
    def has_delete_permission(self, request, obj=None):
        """Kullanıcının cihazı silme yetkisi var mı?"""
        if obj is None:
            return True
        return request.user.is_superuser or request.user.role in ['admin', 'superadmin'] or obj.user == request.user
    
    def has_add_permission(self, request):
        """Kullanıcının cihaz ekleme yetkisi var mı?"""
        return True  # Tüm kullanıcılar cihaz ekleyebilir
    
    def save_model(self, request, obj, form, change):
        """Cihaz kaydedilirken kullanıcı otomatik olarak atanır"""
        if not change:  # Yeni cihaz ekleniyorsa
            obj.user = request.user
        super().save_model(request, obj, form, change)
    
    def get_actions(self, request):
        """Admin kullanıcısının rolüne göre actions'ları filtreler"""
        actions = super().get_actions(request)
        if not request.user.is_superuser and request.user.role not in ['admin', 'superadmin']:
            # Standart kullanıcılar için actions'ları kaldır
            if 'delete_selected' in actions:
                del actions['delete_selected']
        return actions
