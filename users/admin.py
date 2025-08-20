from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from .models import CustomUser, UserLog

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ('tc_kimlik', 'username', 'email', 'first_name', 'last_name', 'role', 'is_active', 'is_locked', 'date_joined', 'profile_image_preview')
    list_filter = ('role', 'is_active', 'is_locked', 'date_joined', 'last_login')
    search_fields = ('tc_kimlik', 'username', 'email', 'first_name', 'last_name')
    ordering = ('-date_joined',)
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Kişisel Bilgiler'), {'fields': ('tc_kimlik', 'first_name', 'last_name', 'email', 'phone', 'profile_image')}),
        (_('Yetkiler'), {
            'fields': ('role', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('Hesap Durumu'), {'fields': ('is_locked', 'failed_login_attempts', 'locked_at')}),
        (_('Önemli tarihler'), {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'tc_kimlik', 'first_name', 'last_name', 'email', 'phone', 'role', 'password1', 'password2'),
        }),
    )
    
    readonly_fields = ('last_login', 'date_joined', 'failed_login_attempts', 'locked_at')
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related()
    
    def unlock_account_action(self, request, queryset):
        """Seçili hesapları açar"""
        updated = queryset.update(is_locked=False, failed_login_attempts=0, locked_at=None)
        self.message_user(request, f'{updated} hesap başarıyla açıldı.')
    unlock_account_action.short_description = "Seçili hesapları aç"
    
    def reset_failed_login_action(self, request, queryset):
        """Başarısız giriş denemelerini sıfırlar"""
        updated = queryset.update(failed_login_attempts=0)
        self.message_user(request, f'{updated} hesabın başarısız giriş denemeleri sıfırlandı.')
    reset_failed_login_action.short_description = "Başarısız giriş denemelerini sıfırla"
    
    def profile_image_preview(self, obj):
        """Profil resmi önizlemesi"""
        if obj.profile_image:
            return f'<img src="{obj.profile_image.url}" width="50" height="50" style="border-radius: 50%; object-fit: cover;" />'
        return f'<div style="width: 50px; height: 50px; border-radius: 50%; background: linear-gradient(45deg, #06b6d4, #3b82f6); display: flex; align-items: center; justify-content: center; color: white; font-weight: bold; font-size: 18px;">{obj.first_name[0] if obj.first_name else "?"}{obj.last_name[0] if obj.last_name else "?"}</div>'
    profile_image_preview.short_description = 'Profil Resmi'
    profile_image_preview.allow_tags = True
    
    actions = [unlock_account_action, reset_failed_login_action]


@admin.register(UserLog)
class UserLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'log_type', 'ip_address', 'created_at')
    list_filter = ('log_type', 'created_at', 'user__role')
    search_fields = ('user__username', 'user__tc_kimlik', 'user__first_name', 'user__last_name', 'description')
    ordering = ('-created_at',)
    readonly_fields = ('user', 'log_type', 'description', 'ip_address', 'user_agent', 'created_at')
    
    fieldsets = (
        (None, {
            'fields': ('user', 'log_type', 'description')
        }),
        (_('Teknik Bilgiler'), {
            'fields': ('ip_address', 'user_agent', 'created_at')
        }),
    )
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')
