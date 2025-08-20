from django import template
from django.db.models import Q

register = template.Library()

@register.filter
def active_devices_count(user):
    """Kullanıcının aktif cihaz sayısını döndürür"""
    return user.device_set.filter(is_active=True).count()

@register.filter
def total_devices_count(user):
    """Kullanıcının toplam cihaz sayısını döndürür"""
    return user.device_set.count()

@register.filter
def inactive_devices_count(user):
    """Kullanıcının pasif cihaz sayısını döndürür"""
    return user.device_set.filter(is_active=False).count()
