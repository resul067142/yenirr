from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q
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

@login_required
def device_list_view(request):
    """Cihaz listesi view'ı"""
    # Kullanıcının yetkisine göre cihazları getir
    if request.user.can_view_all_devices():
        devices = Device.objects.all().select_related('user')
    else:
        devices = Device.objects.filter(user=request.user).select_related('user')
    
    # Filtreleme
    filter_form = DeviceFilterForm(request.GET)
    if filter_form.is_valid():
        device_type = filter_form.cleaned_data.get('device_type')
        is_active = filter_form.cleaned_data.get('is_active')
        date_from = filter_form.cleaned_data.get('date_from')
        date_to = filter_form.cleaned_data.get('date_to')
        search = filter_form.cleaned_data.get('search')
        
        if device_type:
            devices = devices.filter(device_type=device_type)
        
        if is_active:
            if is_active == 'True':
                devices = devices.filter(is_active=True)
            elif is_active == 'False':
                devices = devices.filter(is_active=False)
        
        if date_from:
            devices = devices.filter(created_at__gte=date_from)
        
        if date_to:
            devices = devices.filter(created_at__lte=date_to)
        
        if search:
            devices = devices.filter(
                Q(device_name__icontains=search) |
                Q(gsm_number__icontains=search) |
                Q(device_email__icontains=search) |
                Q(brand__icontains=search) |
                Q(model__icontains=search)
            )
    
    # Sıralama
    sort_by = request.GET.get('sort', '-created_at')
    if sort_by in ['device_name', '-device_name', 'gsm_number', '-gsm_number', 'created_at', '-created_at']:
        devices = devices.order_by(sort_by)
    
    # Sayfalama
    paginator = Paginator(devices, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'filter_form': filter_form,
        'total_devices': devices.count(),
        'can_add_device': request.user.can_manage_devices(),
        'can_export': request.user.can_view_all_devices(),
        'current_filters': request.GET.dict()
    }
    
    return render(request, 'devices/device_list.html', context)

@login_required
def device_add_view(request):
    """Cihaz ekleme view'ı"""
    if not request.user.can_manage_devices():
        messages.error(request, 'Cihaz ekleme yetkiniz yok.')
        return redirect('devices:device_list')
    
    if request.method == 'POST':
        form = DeviceForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    device = form.save(commit=False)
                    device.user = request.user
                    device.save()
                    
                    # Log kaydı
                    UserLog.log_activity(
                        user=request.user,
                        log_type='device_add',
                        description=f'Yeni cihaz eklendi: {device.get_short_info()}',
                        ip_address=get_client_ip(request),
                        user_agent=get_user_agent(request)
                    )
                    
                    messages.success(request, 'Cihaz başarıyla eklendi.')
                    return redirect('devices:device_list')
            except Exception as e:
                messages.error(request, f'Cihaz eklenirken hata oluştu: {str(e)}')
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
    if not request.user.can_view_all_devices() and device.user != request.user:
        messages.error(request, 'Bu cihazı düzenleme yetkiniz yok.')
        return redirect('devices:device_list')
    
    if request.method == 'POST':
        form = DeviceForm(request.POST, instance=device)
        if form.is_valid():
            try:
                with transaction.atomic():
                    form.save()
                    
                    # Log kaydı
                    UserLog.log_activity(
                        user=request.user,
                        log_type='device_update',
                        description=f'Cihaz güncellendi: {device.get_short_info()}',
                        ip_address=get_client_ip(request),
                        user_agent=get_user_agent(request)
                    )
                    
                    messages.success(request, 'Cihaz başarıyla güncellendi.')
                    return redirect('devices:device_list')
            except Exception as e:
                messages.error(request, f'Cihaz güncellenirken hata oluştu: {str(e)}')
    else:
        form = DeviceForm(instance=device)
    
    context = {
        'form': form,
        'device': device,
        'action': 'edit'
    }
    return render(request, 'devices/device_form.html', context)

@login_required
def device_delete_view(request, device_id):
    """Cihaz silme view'ı"""
    device = get_object_or_404(Device, id=device_id)
    
    # Yetki kontrolü
    if not request.user.can_view_all_devices() and device.user != request.user:
        messages.error(request, 'Bu cihazı silme yetkiniz yok.')
        return redirect('devices:device_list')
    
    if request.method == 'POST':
        try:
            device_name = device.get_short_info()
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
        except Exception as e:
            messages.error(request, f'Cihaz silinirken hata oluştu: {str(e)}')
    
    context = {
        'device': device
    }
    return render(request, 'devices/device_confirm_delete.html', context)

@login_required
def device_detail_view(request, device_id):
    """Cihaz detay view'ı"""
    device = get_object_or_404(Device, id=device_id)
    
    # Yetki kontrolü
    if not request.user.can_view_all_devices() and device.user != request.user:
        messages.error(request, 'Bu cihazı görüntüleme yetkiniz yok.')
        return redirect('devices:device_list')
    
    context = {
        'device': device
    }
    return render(request, 'devices/device_detail.html', context)

@login_required
def device_export_csv(request):
    """Cihazları CSV olarak export etme"""
    if not request.user.can_view_all_devices():
        messages.error(request, 'Export yetkiniz yok.')
        return redirect('devices:device_list')
    
    # Kullanıcının yetkisine göre cihazları getir
    if request.user.can_view_all_devices():
        devices = Device.objects.all().select_related('user')
    else:
        devices = Device.objects.filter(user=request.user).select_related('user')
    
    # Filtreleme parametrelerini uygula
    filter_form = DeviceFilterForm(request.GET)
    if filter_form.is_valid():
        device_type = filter_form.cleaned_data.get('device_type')
        is_active = filter_form.cleaned_data.get('is_active')
        date_from = filter_form.cleaned_data.get('date_from')
        date_to = filter_form.cleaned_data.get('date_to')
        search = filter_form.cleaned_data.get('search')
        
        if device_type:
            devices = devices.filter(device_type=device_type)
        
        if is_active:
            if is_active == 'True':
                devices = devices.filter(is_active=True)
            elif is_active == 'False':
                devices = devices.filter(is_active=False)
        
        if date_from:
            devices = devices.filter(created_at__gte=date_from)
        
        if date_to:
            devices = devices.filter(created_at__lte=date_to)
        
        if search:
            devices = devices.filter(
                Q(device_name__icontains=search) |
                Q(gsm_number__icontains=search) |
                Q(device_email__icontains=search) |
                Q(brand__icontains=search) |
                Q(model__icontains=search)
            )
    
    # CSV response oluştur
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="cihazlar_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'
    
    # UTF-8 BOM ekle (Excel uyumluluğu için)
    response.write('\ufeff')
    
    writer = csv.writer(response, delimiter=';')
    
    # Başlık satırı
    if request.user.can_view_all_devices():
        writer.writerow(['Cihaz Adı', 'Cihaz Türü', 'GSM Numarası', 'E-posta', 'Marka', 'Model', 'IMEI', 'Durum', 'Kullanıcı', 'TC Kimlik', 'Kayıt Tarihi'])
    else:
        writer.writerow(['Cihaz Adı', 'Cihaz Türü', 'GSM Numarası', 'E-posta', 'Marka', 'Model', 'IMEI', 'Durum', 'Kayıt Tarihi'])
    
    # Veri satırları
    for device in devices:
        if request.user.can_view_all_devices():
            writer.writerow([
                device.device_name or '',
                device.get_device_type_display_tr(),
                device.gsm_number,
                device.device_email,
                device.brand or '',
                device.model or '',
                device.imei or '',
                'Aktif' if device.is_active else 'Pasif',
                device.user.get_full_name(),
                device.user.tc_kimlik,
                device.created_at.strftime('%d.%m.%Y %H:%M')
            ])
        else:
            writer.writerow([
                device.device_name or '',
                device.get_device_type_display_tr(),
                device.gsm_number,
                device.device_email,
                device.brand or '',
                device.model or '',
                device.imei or '',
                'Aktif' if device.is_active else 'Pasif',
                device.created_at.strftime('%d.%m.%Y %H:%M')
            ])
    
    return response

@login_required
def device_export_json(request):
    """Cihazları JSON olarak export etme"""
    if not request.user.can_view_all_devices():
        messages.error(request, 'Export yetkiniz yok.')
        return redirect('devices:device_list')
    
    # Kullanıcının yetkisine göre cihazları getir
    if request.user.can_view_all_devices():
        devices = Device.objects.all().select_related('user')
    else:
        devices = Device.objects.filter(user=request.user).select_related('user')
    
    # Filtreleme parametrelerini uygula (CSV ile aynı)
    filter_form = DeviceFilterForm(request.GET)
    if filter_form.is_valid():
        device_type = filter_form.cleaned_data.get('device_type')
        is_active = filter_form.cleaned_data.get('is_active')
        date_from = filter_form.cleaned_data.get('date_from')
        date_to = filter_form.cleaned_data.get('date_to')
        search = filter_form.cleaned_data.get('search')
        
        if device_type:
            devices = devices.filter(device_type=device_type)
        
        if is_active:
            if is_active == 'True':
                devices = devices.filter(is_active=True)
            elif is_active == 'False':
                devices = devices.filter(is_active=False)
        
        if date_from:
            devices = devices.filter(created_at__gte=date_from)
        
        if date_to:
            devices = devices.filter(created_at__lte=date_to)
        
        if search:
            devices = devices.filter(
                Q(device_name__icontains=search) |
                Q(gsm_number__icontains=search) |
                Q(device_email__icontains=search) |
                Q(brand__icontains=search) |
                Q(model__icontains=search)
            )
    
    # JSON response oluştur
    response = HttpResponse(content_type='application/json; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="cihazlar_{timezone.now().strftime("%Y%m%d_%H%M%S")}.json"'
    
    data = []
    for device in devices:
        device_data = {
            'id': device.id,
            'device_name': device.device_name or '',
            'device_type': device.get_device_type_display_tr(),
            'gsm_number': device.gsm_number,
            'device_email': device.device_email,
            'brand': device.brand or '',
            'model': device.model or '',
            'imei': device.imei or '',
            'is_active': device.is_active,
            'created_at': device.created_at.strftime('%d.%m.%Y %H:%M'),
            'updated_at': device.updated_at.strftime('%d.%m.%Y %H:%M')
        }
        
        if request.user.can_view_all_devices():
            device_data.update({
                'user': {
                    'id': device.user.id,
                    'full_name': device.user.get_full_name(),
                    'tc_kimlik': device.user.tc_kimlik,
                    'email': device.user.email
                }
            })
        
        data.append(device_data)
    
    response.write(json.dumps(data, ensure_ascii=False, indent=2))
    return response

@csrf_exempt
@require_http_methods(["POST"])
@login_required
def device_toggle_status(request, device_id):
    """Cihaz durumunu değiştirme (AJAX)"""
    device = get_object_or_404(Device, id=device_id)
    
    # Yetki kontrolü
    if not request.user.can_view_all_devices() and device.user != request.user:
        return JsonResponse({'error': 'Yetkiniz yok'}, status=403)
    
    try:
        device.is_active = not device.is_active
        device.save()
        
        # Log kaydı
        status_text = 'aktif' if device.is_active else 'pasif'
        UserLog.log_activity(
            user=request.user,
            log_type='device_update',
            description=f'Cihaz durumu {status_text} yapıldı: {device.get_short_info()}',
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request)
        )
        
        return JsonResponse({
            'success': True,
            'is_active': device.is_active,
            'status_text': 'Aktif' if device.is_active else 'Pasif'
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def device_statistics_view(request):
    """Cihaz istatistikleri view'ı"""
    # Kullanıcının yetkisine göre cihazları getir
    if request.user.can_view_all_devices():
        devices = Device.objects.all()
    else:
        devices = Device.objects.filter(user=request.user)
    
    # Genel istatistikler
    total_devices = devices.count()
    active_devices = devices.filter(is_active=True).count()
    inactive_devices = devices.filter(is_active=False).count()
    
    # Cihaz türüne göre dağılım
    device_type_stats = {}
    for device_type, display_name in Device.DEVICE_TYPE_CHOICES:
        count = devices.filter(device_type=device_type).count()
        if count > 0:
            device_type_stats[display_name] = count
    
    # Son 7 günlük kayıtlar
    last_7_days = []
    for i in range(7):
        date = timezone.now().date() - timedelta(days=i)
        count = devices.filter(created_at__date=date).count()
        last_7_days.append({
            'date': date.strftime('%d.%m'),
            'count': count
        })
    last_7_days.reverse()
    
    # Kullanıcı başına cihaz ortalaması
    if request.user.can_view_all_devices():
        total_users = User.objects.filter(is_active=True).count()
        avg_devices_per_user = total_devices / total_users if total_users > 0 else 0
    else:
        avg_devices_per_user = total_devices
    
    context = {
        'total_devices': total_devices,
        'active_devices': active_devices,
        'inactive_devices': inactive_devices,
        'device_type_stats': device_type_stats,
        'last_7_days': last_7_days,
        'avg_devices_per_user': round(avg_devices_per_user, 1),
        'can_view_all': request.user.can_view_all_devices()
    }
    
    return render(request, 'devices/device_statistics.html', context)
