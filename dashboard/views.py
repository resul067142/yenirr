from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
import json
import platform
import django
from datetime import datetime, timedelta
from users.models import CustomUser, UserLog
from devices.models import Device
from django.db.models import Count, Q
from django.utils import timezone

@login_required
def home_view(request):
    """Ana dashboard view'ı"""
    user = request.user
    
    # Kullanıcının yetkisine göre veri getir
    if user.can_view_all_devices:
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
    """İstatistikler view'ı"""
    user = request.user
    
    if user.can_view_all_devices:
        # Admin için tüm veriler
        total_users = CustomUser.objects.filter(is_active=True).count()
        total_devices = Device.objects.count()
        active_devices = Device.objects.filter(is_active=True).count()
        inactive_devices = Device.objects.filter(is_active=False).count()
        locked_accounts = CustomUser.objects.filter(is_locked=True).count()
        
        # Kullanıcı başına cihaz ortalaması
        avg_devices_per_user = total_devices / total_users if total_users > 0 else 0
        
        # Son 7 günlük kullanıcı kayıtları
        last_7_days_users = []
        for i in range(7):
            date = timezone.now().date() - timedelta(days=i)
            count = CustomUser.objects.filter(date_joined__date=date).count()
            last_7_days_users.append({'date': date.strftime('%d.%m'), 'count': count})
        last_7_days_users.reverse()
        
        # Son 7 günlük cihaz kayıtları
        last_7_days_devices = []
        for i in range(7):
            date = timezone.now().date() - timedelta(days=i)
            count = Device.objects.filter(created_at__date=date).count()
            last_7_days_devices.append({'date': date.strftime('%d.%m'), 'count': count})
        last_7_days_devices.reverse()
        
        # Chart.js için veri formatları
        user_role_labels = []
        user_role_data = []
        for role, display_name in CustomUser.ROLE_CHOICES:
            count = CustomUser.objects.filter(role=role, is_active=True).count()
            if count > 0:
                user_role_labels.append(display_name)
                user_role_data.append(count)
        
        device_type_labels = []
        device_type_data = []
        for device_type, display_name in Device.DEVICE_TYPE_CHOICES:
            count = Device.objects.filter(device_type=device_type).count()
            if count > 0:
                device_type_labels.append(display_name)
                device_type_data.append(count)
        
        # En çok cihaza sahip kullanıcılar
        top_users = CustomUser.objects.annotate(
            device_count=Count('devices')
        ).filter(device_count__gt=0).order_by('-device_count')[:5]
        
        # Son aktiviteler
        recent_activities = UserLog.objects.select_related('user').order_by('-created_at')[:5]
        
        context = {
            'total_users': total_users,
            'total_devices': total_devices,
            'active_devices': active_devices,
            'inactive_devices': inactive_devices,
            'locked_accounts': locked_accounts,
            'avg_devices_per_user': round(avg_devices_per_user, 1),
            'user_role_labels': user_role_labels,
            'user_role_data': user_role_data,
            'device_type_labels': device_type_labels,
            'device_type_data': device_type_data,
            'weekly_user_labels': [item['date'] for item in last_7_days_users],
            'weekly_user_data': [item['count'] for item in last_7_days_users],
            'weekly_device_labels': [item['date'] for item in last_7_days_devices],
            'weekly_device_data': [item['count'] for item in last_7_days_devices],
            'top_users': top_users,
            'recent_activities': recent_activities,
            'is_admin': True
        }
    else:
        # Standart kullanıcı için sadece kendi verileri
        user_devices = Device.objects.filter(user=user)
        total_devices = user_devices.count()
        active_devices = user_devices.filter(is_active=True).count()
        inactive_devices = user_devices.filter(is_active=False).count()
        
        # Son 7 günlük cihaz kayıtları (kullanıcının kendi cihazları)
        last_7_days_devices = []
        for i in range(7):
            date = timezone.now().date() - timedelta(days=i)
            count = user_devices.filter(created_at__date=date).count()
            last_7_days_devices.append({'date': date.strftime('%d.%m'), 'count': count})
        last_7_days_devices.reverse()
        
        # Cihaz türüne göre dağılım (kullanıcının kendi cihazları)
        device_type_labels = []
        device_type_data = []
        for device_type, display_name in Device.DEVICE_TYPE_CHOICES:
            count = user_devices.filter(device_type=device_type).count()
            if count > 0:
                device_type_labels.append(display_name)
                device_type_data.append(count)
        
        # Son aktiviteler (kullanıcının kendi aktiviteleri)
        recent_activities = UserLog.objects.filter(user=user).order_by('-created_at')[:5]
        
        context = {
            'total_devices': total_devices,
            'active_devices': active_devices,
            'inactive_devices': inactive_devices,
            'device_type_labels': device_type_labels,
            'device_type_data': device_type_data,
            'weekly_device_labels': [item['date'] for item in last_7_days_devices],
            'weekly_device_data': [item['count'] for item in last_7_days_devices],
            'recent_activities': recent_activities,
            'is_admin': False
        }
    
    return render(request, 'dashboard/statistics.html', context)

def activity_log_view(request):
    """Aktivite logları view'ı"""
    user = request.user
    
    # Kullanıcının yetkisine göre logları getir
    if hasattr(request, 'user') and request.user.is_authenticated:
        if user.can_view_all_devices:
            logs = UserLog.objects.all().select_related('user').order_by('-created_at')
        else:
            logs = UserLog.objects.filter(user=user).order_by('-created_at')
    else:
        # Anonymous user için tüm logları göster
        logs = UserLog.objects.all().select_related('user').order_by('-created_at')
    
    # Filtreleme
    log_type_filter = request.GET.get('log_type')
    user_filter = request.GET.get('user')
    start_date_filter = request.GET.get('start_date')
    end_date_filter = request.GET.get('end_date')
    
    if log_type_filter:
        logs = logs.filter(log_type=log_type_filter)
    
    if user_filter:
        try:
            user_id = int(user_filter)
            logs = logs.filter(user_id=user_id)
        except ValueError:
            pass
    
    if start_date_filter:
        try:
            start_date = datetime.strptime(start_date_filter, '%Y-%m-%d').date()
            logs = logs.filter(created_at__date__gte=start_date)
        except ValueError:
            pass
    
    if end_date_filter:
        try:
            end_date = datetime.strptime(end_date_filter, '%Y-%m-%d').date()
            logs = logs.filter(created_at__date__lte=end_date)
        except ValueError:
            pass
    
    # Sayfalama
    paginator = Paginator(logs, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # İstatistikler
    total_logs = logs.count()
    
    # Bugün, bu hafta, bu ay istatistikleri
    today = timezone.now().date()
    week_start = today - timedelta(days=today.weekday())
    month_start = today.replace(day=1)
    
    today_logs = logs.filter(created_at__date=today).count()
    week_logs = logs.filter(created_at__date__gte=week_start).count()
    month_logs = logs.filter(created_at__date__gte=month_start).count()
    
    # Kullanıcı listesi (filtre için)
    users = CustomUser.objects.all().order_by('username')
    
    # Filtreler
    filters = {
        'start_date': request.GET.get('start_date', ''),
        'end_date': request.GET.get('end_date', ''),
        'log_type': request.GET.get('log_type', ''),
        'user': request.GET.get('user', ''),
    }
    
    context = {
        'page_obj': page_obj,
        'is_admin': user.can_view_all_devices,
        'total_logs': total_logs,
        'today_logs': today_logs,
        'week_logs': week_logs,
        'month_logs': month_logs,
        'users': users,
        'filters': filters
    }
    
    return render(request, 'dashboard/activity_log.html', context)

@login_required
def system_info_view(request):
    """Sistem bilgileri view'ı (sadece admin'ler için)"""
    if not request.user.can_view_all_devices:
        messages.error(request, 'Bu sayfaya erişim yetkiniz yok.')
        return redirect('dashboard:home')
    
    # Sistem bilgileri
    system_info = {
        'python_version': platform.python_version(),
        'django_version': django.get_version(),
        'os': platform.system(),
        'os_version': platform.release(),
        'cpu_count': 'N/A',  # psutil olmadan
        'memory_total': 'N/A',  # psutil olmadan
        'memory_available': 'N/A',  # psutil olmadan
        'disk_usage': 'N/A'  # psutil olmadan
    }
    
    context = {
        'system_info': system_info,
        'is_admin': True
    }
    
    return render(request, 'dashboard/system_info.html', context)

@login_required
def admin_panel_view(request):
    """Yönetim paneli view'ı (sadece admin'ler için)"""
    if not request.user.can_view_all_devices:
        messages.error(request, 'Bu sayfaya erişim yetkiniz yok.')
        return redirect('dashboard:home')
    
    # Sistem istatistikleri
    total_users = CustomUser.objects.filter(is_active=True).count()
    total_devices = Device.objects.count()
    locked_accounts = CustomUser.objects.filter(is_locked=True).count()
    
    # Aktif oturum sayısı (yaklaşık)
    active_sessions = 1  # Şu anda giriş yapmış kullanıcı
    
    # Son aktiviteler
    recent_activities = UserLog.objects.select_related('user').order_by('-created_at')[:10]
    
    context = {
        'total_users': total_users,
        'total_devices': total_devices,
        'locked_accounts': locked_accounts,
        'active_sessions': active_sessions,
        'recent_activities': recent_activities,
        'is_admin': True
    }
    
    return render(request, 'dashboard/admin_panel.html', context)

@login_required
@require_http_methods(["GET"])
def log_detail_api(request, log_id):
    """Log detaylarını API olarak döndür"""
    try:
        log = get_object_or_404(UserLog, id=log_id)
        
        # Kullanıcının bu log'u görme yetkisi var mı kontrol et
        if not request.user.can_view_all_devices and log.user != request.user:
            return JsonResponse({'error': 'Yetkisiz erişim'}, status=403)
        
        data = {
            'id': log.id,
            'user_name': log.user.get_full_name() or log.user.username,
            'log_type': log.log_type,
            'log_type_display': log.get_log_type_display(),
            'description': log.description or '',
            'additional_data': log.additional_data or '',
            'ip_address': log.ip_address or '',
            'user_agent': getattr(log, 'user_agent', '') or '',
            'created_at': log.created_at.strftime('%d.%m.%Y %H:%M:%S'),
        }
        
        return JsonResponse(data)
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@require_http_methods(["POST"])
def log_delete_api(request, log_id):
    """Log kaydını sil"""
    try:
        # Sadece admin'ler silebilir
        if not request.user.can_view_all_devices:
            return JsonResponse({'error': 'Yetkisiz erişim'}, status=403)
        
        log = get_object_or_404(UserLog, id=log_id)
        log.delete()
        
        return JsonResponse({'success': True, 'message': 'Log kaydı başarıyla silindi'})
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
