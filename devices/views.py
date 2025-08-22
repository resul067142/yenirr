from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.utils import timezone
from django.db import transaction
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import get_user_model
from datetime import datetime, timedelta
import csv
import json
from .models import Device
from .forms import DeviceForm, DeviceFilterForm
from users.models import UserLog

User = get_user_model()

def get_client_ip(request):
    """Kullanıcının IP adresini alır"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def get_user_agent(request):
    """Kullanıcının tarayıcı bilgisini alır"""
    return request.META.get('HTTP_USER_AGENT', '')

def device_list_view(request):
    """Cihaz listesi view'ı"""
    # Kullanıcının yetkilerine göre cihazları getir
    if hasattr(request, 'user') and request.user.is_authenticated:
        if request.user.can_view_all_devices:
            devices = Device.objects.all()
        else:
            devices = Device.objects.filter(user=request.user)
    else:
        # Anonymous user için tüm cihazları göster
        devices = Device.objects.all()
    
    # Filtreleme
    device_type_filter = request.GET.get('device_type')
    status_filter = request.GET.get('status')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    search_query = request.GET.get('search')
    
    if device_type_filter:
        devices = devices.filter(device_type=device_type_filter)
    
    if status_filter == 'active':
        devices = devices.filter(is_active=True)
    elif status_filter == 'inactive':
        devices = devices.filter(is_active=False)
    
    if start_date:
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            devices = devices.filter(created_at__date__gte=start_date)
        except ValueError:
            pass
    
    if end_date:
        try:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            devices = devices.filter(created_at__date__lte=end_date)
        except ValueError:
            pass
    
    if search_query:
        devices = devices.filter(
            Q(device_name__icontains=search_query) |
            Q(gsm_number__icontains=search_query) |
            Q(device_email__icontains=search_query) |
            Q(brand__icontains=search_query) |
            Q(model__icontains=search_query)
        )
    
    # Sıralama
    sort_by = request.GET.get('sort', '-created_at')
    if sort_by in ['device_name', '-device_name', 'created_at', '-created_at', 'device_type', '-device_type']:
        devices = devices.order_by(sort_by)
    
    # Sayfalama
    paginator = Paginator(devices, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # İstatistikler
    total_devices = devices.count()
    active_devices = devices.filter(is_active=True).count()
    inactive_devices = devices.filter(is_active=False).count()
    
    # Cihaz türü dağılımı
    device_type_stats = devices.values('device_type').annotate(count=Count('id')).order_by('-count')
    
    context = {
        'page_obj': page_obj,
        'devices': page_obj,  # Template'de kullanım için
        'device_types': Device.DEVICE_TYPE_CHOICES,
        'total_devices': total_devices,
        'active_devices': active_devices,
        'inactive_devices': inactive_devices,
        'device_type_stats': device_type_stats,
        'current_filters': {
            'device_type': device_type_filter,
            'status': status_filter,
            'start_date': start_date,
            'end_date': end_date,
            'search': search_query,
            'sort': sort_by
        }
    }
    
    return render(request, 'devices/device_list.html', context)

@login_required
def device_add_view(request):
    """Cihaz ekleme view'ı"""
    if not request.user.can_manage_devices:
        messages.error(request, 'Cihaz ekleme yetkiniz yok.')
        return redirect('devices:device_list')
    
    if request.method == 'POST':
        form = DeviceForm(request.POST, request.FILES)
        if form.is_valid():
            device = form.save(commit=False)
            device.user = request.user
            device.save()
            
            # Log kaydı
            UserLog.log_activity(
                user=request.user,
                log_type='device_add',
                description=f'Yeni cihaz eklendi: {device.device_name}',
                ip_address=get_client_ip(request),
                user_agent=get_user_agent(request)
            )
            
            messages.success(request, 'Cihaz başarıyla eklendi.')
            return redirect('devices:device_detail', device_id=device.id)
    else:
        form = DeviceForm()
    
    context = {
        'form': form,
        'action': 'add'
    }
    
    return render(request, 'devices/device_form.html', context)

@login_required
def device_edit_view(request, device_id):
    """Cihaz düzenleme view'ı"""
    device = get_object_or_404(Device, id=device_id)
    
    # Yetki kontrolü
    if not request.user.can_view_all_devices and device.user != request.user:
        messages.error(request, 'Bu cihazı düzenleme yetkiniz yok.')
        return redirect('devices:device_list')
    
    if request.method == 'POST':
        form = DeviceForm(request.POST, request.FILES, instance=device)
        if form.is_valid():
            device = form.save(commit=False)
            device.user = request.user
            device.save()
            
            # Log kaydı
            UserLog.log_activity(
                user=request.user,
                log_type='device_edit',
                description=f'Cihaz düzenlendi: {device.device_name}',
                ip_address=get_client_ip(request),
                user_agent=get_user_agent(request)
            )
            
            messages.success(request, 'Cihaz başarıyla güncellendi.')
            return redirect('devices:device_detail', device_id=device.id)
    else:
        form = DeviceForm(instance=device)
    
    context = {
        'form': form,
        'device': device
    }
    
    return render(request, 'devices/device_form.html', context)

@login_required
def device_delete_view(request, device_id):
    """Cihaz silme view'ı"""
    device = get_object_or_404(Device, id=device_id)
    
    # Yetki kontrolü
    if not request.user.can_view_all_devices and device.user != request.user:
        messages.error(request, 'Bu cihazı silme yetkiniz yok.')
        return redirect('devices:device_list')
    
    if request.method == 'POST':
        device_name = device.device_name
        device.delete()
        
        # Log kaydı
        UserLog.log_activity(
            user=request.user,
            log_type='device_delete',
            description=f'Cihaz silindi: {device_name}',
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request)
        )
        
        messages.success(request, 'Cihaz başarıyla silindi.')
        return redirect('devices:device_list')
    
    context = {
        'device': device
    }
    
    return render(request, 'devices/device_delete.html', context)

@login_required
def device_detail_view(request, device_id):
    """Cihaz detay view'ı"""
    device = get_object_or_404(Device, id=device_id)
    
    # Yetki kontrolü
    if not request.user.can_view_all_devices and device.user != request.user:
        messages.error(request, 'Bu cihaza erişim yetkiniz yok.')
        return redirect('devices:device_list')
    
    context = {
        'device': device,
        'can_edit': request.user.can_manage_devices or device.user == request.user,
        'can_delete': request.user.can_manage_devices or device.user == request.user
    }
    
    return render(request, 'devices/device_detail.html', context)

@login_required
def device_export_csv(request):
    """Cihaz verilerini CSV formatında dışa aktar"""
    if not request.user.can_view_all_devices:
        messages.error(request, 'Bu işlem için yetkiniz yok.')
        return redirect('devices:device_list')
    
    # Kullanıcının yetkisine göre cihazları getir
    if request.user.can_view_all_devices:
        devices = Device.objects.all()
    else:
        devices = Device.objects.filter(user=request.user)
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="cihazlar.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Cihaz Adı', 'Tür', 'GSM Numarası', 'E-posta', 'Kullanıcı', 'Durum', 'Kayıt Tarihi'])
    
    for device in devices:
        writer.writerow([
            device.device_name or 'İsimsiz',
            device.get_device_type_display(),
            device.gsm_number or '',
            device.device_email or '',
            device.user.get_full_name(),
            'Aktif' if device.is_active else 'Pasif',
            device.created_at.strftime('%d.%m.%Y %H:%M')
        ])
    
    return response

@login_required
def device_export_json(request):
    """Cihaz verilerini JSON formatında dışa aktar"""
    if not request.user.can_view_all_devices:
        messages.error(request, 'Bu işlem için yetkiniz yok.')
        return redirect('devices:device_list')
    
    # Kullanıcının yetkisine göre cihazları getir
    if request.user.can_view_all_devices:
        devices = Device.objects.all()
    else:
        devices = Device.objects.filter(user=request.user)
    
    data = []
    for device in devices:
        data.append({
            'id': device.id,
            'device_name': device.device_name or 'İsimsiz',
            'device_type': device.get_device_type_display(),
            'gsm_number': device.gsm_number or '',
            'device_email': device.device_email or '',
            'user': device.user.get_full_name(),
            'is_active': device.is_active,
            'created_at': device.created_at.strftime('%d.%m.%Y %H:%M')
        })
    
    return JsonResponse(data, safe=False)

@csrf_exempt
@require_http_methods(["POST"])
@login_required
def device_toggle_status(request, device_id):
    """Cihaz durumunu değiştir (AJAX)"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Sadece POST metodu desteklenir'}, status=405)
    
    device = get_object_or_404(Device, id=device_id)
    
    # Yetki kontrolü
    if not request.user.can_view_all_devices and device.user != request.user:
        return JsonResponse({'error': 'Bu işlem için yetkiniz yok'}, status=403)
    
    try:
        device.is_active = not device.is_active
        device.save()
        
        # Log kaydı
        status_text = 'aktif' if device.is_active else 'pasif'
        UserLog.log_activity(
            user=request.user,
            log_type='device_status_change',
            description=f'Cihaz durumu değiştirildi: {device.device_name} -> {status_text}',
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request)
        )
        
        return JsonResponse({
            'success': True,
            'is_active': device.is_active,
            'message': f'Cihaz {status_text} yapıldı'
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def device_statistics_view(request):
    """Cihaz istatistikleri view'ı"""
    if not request.user.can_view_all_devices:
        messages.error(request, 'Bu sayfaya erişim yetkiniz yok.')
        return redirect('devices:device_list')
    
    # Tüm cihazları getir
    devices = Device.objects.all()
    
    # Genel istatistikler
    total_devices = devices.count()
    active_devices = devices.filter(is_active=True).count()
    inactive_devices = devices.filter(is_active=False).count()
    
    # Cihaz türüne göre dağılım
    device_type_stats = devices.values('device_type').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Kullanıcıya göre cihaz dağılımı
    user_device_stats = devices.values('user__first_name', 'user__last_name').annotate(
        count=Count('id')
    ).order_by('-count')[:10]
    
    # Son 30 günlük cihaz kayıtları
    thirty_days_ago = timezone.now().date() - timedelta(days=30)
    daily_registrations = []
    
    for i in range(30):
        date = thirty_days_ago + timedelta(days=i)
        count = devices.filter(created_at__date=date).count()
        daily_registrations.append({
            'date': date.strftime('%d.%m'),
            'count': count
        })
    
    context = {
        'total_devices': total_devices,
        'active_devices': active_devices,
        'inactive_devices': inactive_devices,
        'device_type_stats': device_type_stats,
        'user_device_stats': user_device_stats,
        'daily_registrations': daily_registrations
    }
    
    return render(request, 'devices/device_statistics.html', context)
