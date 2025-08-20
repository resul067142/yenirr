from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q
from django.utils import timezone
from datetime import datetime, timedelta
from users.models import CustomUser, UserLog
from devices.models import Device

@login_required
def home_view(request):
    """Ana dashboard view'ı"""
    user = request.user
    
    # Kullanıcının yetkisine göre veri getir
    if user.can_view_all_devices():
        # Admin için tüm veriler
        total_users = CustomUser.objects.filter(is_active=True).count()
        total_devices = Device.objects.count()
        active_devices = Device.objects.filter(is_active=True).count()
        inactive_devices = Device.objects.filter(is_active=False).count()
        
        # Son 7 günlük yeni kullanıcılar
        last_7_days_users = []
        for i in range(7):
            date = timezone.now().date() - timedelta(days=i)
            count = CustomUser.objects.filter(date_joined__date=date).count()
            last_7_days_users.append({
                'date': date.strftime('%d.%m'),
                'count': count
            })
        last_7_days_users.reverse()
        
        # Son 7 günlük yeni cihazlar
        last_7_days_devices = []
        for i in range(7):
            date = timezone.now().date() - timedelta(days=i)
            count = Device.objects.filter(created_at__date=date).count()
            last_7_days_devices.append({
                'date': date.strftime('%d.%m'),
                'count': count
            })
        last_7_days_devices.reverse()
        
        # Cihaz türüne göre dağılım
        device_type_stats = {}
        for device_type, display_name in Device.DEVICE_TYPE_CHOICES:
            count = Device.objects.filter(device_type=device_type).count()
            if count > 0:
                device_type_stats[display_name] = count
        
        # Kullanıcı rolüne göre dağılım
        user_role_stats = {}
        for role, display_name in CustomUser.ROLE_CHOICES:
            count = CustomUser.objects.filter(role=role, is_active=True).count()
            if count > 0:
                user_role_stats[display_name] = count
        
        # Son aktiviteler (son 10 log)
        recent_activities = UserLog.objects.select_related('user').order_by('-created_at')[:10]
        
        # Kullanıcı başına cihaz ortalaması
        avg_devices_per_user = total_devices / total_users if total_users > 0 else 0
        
        # Kilitli hesaplar
        locked_accounts = CustomUser.objects.filter(is_locked=True).count()
        
        context = {
            'total_users': total_users,
            'total_devices': total_devices,
            'active_devices': active_devices,
            'inactive_devices': inactive_devices,
            'avg_devices_per_user': round(avg_devices_per_user, 1),
            'locked_accounts': locked_accounts,
            'device_type_stats': device_type_stats,
            'user_role_stats': user_role_stats,
            'last_7_days_users': last_7_days_users,
            'last_7_days_devices': last_7_days_devices,
            'recent_activities': recent_activities,
            'is_admin': True
        }
        
    else:
        # Standart kullanıcı için sadece kendi verileri
        user_devices = Device.objects.filter(user=user)
        total_devices = user_devices.count()
        active_devices = user_devices.filter(is_active=True).count()
        inactive_devices = user_devices.filter(is_active=False).count()
        
        # Son 7 günlük yeni cihazlar (kullanıcının kendi cihazları)
        last_7_days_devices = []
        for i in range(7):
            date = timezone.now().date() - timedelta(days=i)
            count = user_devices.filter(created_at__date=date).count()
            last_7_days_devices.append({
                'date': date.strftime('%d.%m'),
                'count': count
            })
        last_7_days_devices.reverse()
        
        # Cihaz türüne göre dağılım (kullanıcının kendi cihazları)
        device_type_stats = {}
        for device_type, display_name in Device.DEVICE_TYPE_CHOICES:
            count = user_devices.filter(device_type=device_type).count()
            if count > 0:
                device_type_stats[display_name] = count
        
        # Son aktiviteler (kullanıcının kendi logları)
        recent_activities = UserLog.objects.filter(user=user).order_by('-created_at')[:10]
        
        context = {
            'total_devices': total_devices,
            'active_devices': active_devices,
            'inactive_devices': inactive_devices,
            'device_type_stats': device_type_stats,
            'last_7_days_devices': last_7_days_devices,
            'recent_activities': recent_activities,
            'is_admin': False
        }
    
    return render(request, 'dashboard/home.html', context)

@login_required
def statistics_view(request):
    """Detaylı istatistikler view'ı"""
    user = request.user
    
    if user.can_view_all_devices():
        # Admin için tüm istatistikler
        total_users = CustomUser.objects.filter(is_active=True).count()
        total_devices = Device.objects.count()
        
        # Cihaz türüne göre detaylı dağılım
        device_type_detailed = Device.objects.values('device_type').annotate(
            count=Count('id')
        ).order_by('-count')
        
        # Kullanıcı rolüne göre detaylı dağılım
        user_role_detailed = CustomUser.objects.filter(is_active=True).values('role').annotate(
            count=Count('id')
        ).order_by('-count')
        
        # Aylık kayıt istatistikleri (son 12 ay)
        monthly_stats = []
        for i in range(12):
            date = timezone.now().date() - timedelta(days=30*i)
            month_start = date.replace(day=1)
            month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
            
            users_count = CustomUser.objects.filter(
                date_joined__date__range=[month_start, month_end]
            ).count()
            
            devices_count = Device.objects.filter(
                created_at__date__range=[month_start, month_end]
            ).count()
            
            monthly_stats.append({
                'month': month_start.strftime('%B %Y'),
                'users': users_count,
                'devices': devices_count
            })
        
        monthly_stats.reverse()
        
        # En aktif kullanıcılar (en çok cihazı olan)
        top_users = CustomUser.objects.annotate(
            device_count=Count('devices')
        ).filter(device_count__gt=0).order_by('-device_count')[:10]
        
        # En çok kullanılan cihaz türleri
        top_device_types = Device.objects.values('device_type').annotate(
            count=Count('id')
        ).order_by('-count')[:5]
        
        context = {
            'total_users': total_users,
            'total_devices': total_devices,
            'device_type_detailed': device_type_detailed,
            'user_role_detailed': user_role_detailed,
            'monthly_stats': monthly_stats,
            'top_users': top_users,
            'top_device_types': top_device_types,
            'is_admin': True
        }
        
    else:
        # Standart kullanıcı için sadece kendi istatistikleri
        user_devices = Device.objects.filter(user=user)
        total_devices = user_devices.count()
        
        # Cihaz türüne göre detaylı dağılım
        device_type_detailed = user_devices.values('device_type').annotate(
            count=Count('id')
        ).order_by('-count')
        
        # Aylık cihaz ekleme istatistikleri (son 12 ay)
        monthly_stats = []
        for i in range(12):
            date = timezone.now().date() - timedelta(days=30*i)
            month_start = date.replace(day=1)
            month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
            
            devices_count = user_devices.filter(
                created_at__date__range=[month_start, month_end]
            ).count()
            
            monthly_stats.append({
                'month': month_start.strftime('%B %Y'),
                'devices': devices_count
            })
        
        monthly_stats.reverse()
        
        context = {
            'total_devices': total_devices,
            'device_type_detailed': device_type_detailed,
            'monthly_stats': monthly_stats,
            'is_admin': False
        }
    
    return render(request, 'dashboard/statistics.html', context)

@login_required
def activity_log_view(request):
    """Aktivite logları view'ı"""
    user = request.user
    
    if user.can_view_all_devices():
        # Admin için tüm loglar
        logs = UserLog.objects.select_related('user').order_by('-created_at')
    else:
        # Standart kullanıcı için sadece kendi logları
        logs = UserLog.objects.filter(user=user).order_by('-created_at')
    
    # Filtreleme
    log_type_filter = request.GET.get('log_type')
    if log_type_filter:
        logs = logs.filter(log_type=log_type_filter)
    
    date_from = request.GET.get('date_from')
    if date_from:
        try:
            date_from = datetime.strptime(date_from, '%Y-%m-%d').date()
            logs = logs.filter(created_at__date__gte=date_from)
        except ValueError:
            pass
    
    date_to = request.GET.get('date_to')
    if date_to:
        try:
            date_to = datetime.strptime(date_to, '%Y-%m-%d').date()
            logs = logs.filter(created_at__date__lte=date_to)
        except ValueError:
            pass
    
    # Sayfalama
    from django.core.paginator import Paginator
    paginator = Paginator(logs, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Log türleri için choices
    log_types = UserLog.LOG_TYPE_CHOICES
    
    context = {
        'page_obj': page_obj,
        'log_types': log_types,
        'current_filters': {
            'log_type': log_type_filter,
            'date_from': date_from,
            'date_to': date_to
        },
        'is_admin': user.can_view_all_devices()
    }
    
    return render(request, 'dashboard/activity_log.html', context)

@login_required
def system_info_view(request):
    """Sistem bilgileri view'ı (sadece admin'ler için)"""
    if not request.user.can_view_all_devices():
        messages.error(request, 'Bu sayfaya erişim yetkiniz yok.')
        return redirect('dashboard:home')
    
    # Sistem istatistikleri
    total_users = CustomUser.objects.count()
    active_users = CustomUser.objects.filter(is_active=True).count()
    locked_users = CustomUser.objects.filter(is_locked=True).count()
    
    total_devices = Device.objects.count()
    active_devices = Device.objects.filter(is_active=True).count()
    
    # Son 24 saat aktivite
    last_24_hours = timezone.now() - timedelta(hours=24)
    recent_logins = UserLog.objects.filter(
        log_type='login',
        created_at__gte=last_24_hours
    ).count()
    
    recent_failed_logins = UserLog.objects.filter(
        log_type='login_failed',
        created_at__gte=last_24_hours
    ).count()
    
    recent_device_adds = UserLog.objects.filter(
        log_type='device_add',
        created_at__gte=last_24_hours
    ).count()
    
    # Veritabanı boyutu (yaklaşık)
    user_count = CustomUser.objects.count()
    device_count = Device.objects.count()
    log_count = UserLog.objects.count()
    
    estimated_db_size = (user_count * 1024) + (device_count * 512) + (log_count * 256)  # bytes
    
    context = {
        'total_users': total_users,
        'active_users': active_users,
        'locked_users': locked_users,
        'total_devices': total_devices,
        'active_devices': active_devices,
        'recent_logins': recent_logins,
        'recent_failed_logins': recent_failed_logins,
        'recent_device_adds': recent_device_adds,
        'estimated_db_size': estimated_db_size,
        'estimated_db_size_mb': round(estimated_db_size / (1024 * 1024), 2)
    }
    
    return render(request, 'dashboard/system_info.html', context)
