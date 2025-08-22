from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.core.paginator import Paginator
from django.db import transaction
from .models import CustomUser, UserLog, QuickAction
from .forms import CustomUserCreationForm, CustomUserUpdateForm, CustomAuthenticationForm, PasswordChangeForm
from django.utils import timezone
from django.db.models import Q

def get_client_ip(request):
    """Client IP adresini alır"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def get_user_agent(request):
    """User agent bilgisini alır"""
    return request.META.get('HTTP_USER_AGENT', '')

def register_view(request):
    """Kullanıcı kayıt view'ı"""
    if request.user.is_authenticated:
        return redirect('dashboard:home')
    
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password1'])
            user.save()
            
            # Log kaydı
            UserLog.log_activity(
                user=user,
                log_type='user_registered',
                description='Yeni kullanıcı kaydı oluşturuldu',
                ip_address=get_client_ip(request),
                user_agent=get_user_agent(request)
            )
            
            messages.success(request, 'Hesabınız başarıyla oluşturuldu. Şimdi giriş yapabilirsiniz.')
            return redirect('users:login')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'users/register.html', {'form': form})

def login_view(request):
    """Kullanıcı giriş view'ı"""
    if request.user.is_authenticated:
        return redirect('dashboard:home')
    
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            
            if user is not None:
                if user.is_locked:
                    messages.error(request, 'Hesabınız kilitli. Lütfen yönetici ile iletişime geçin.')
                    return redirect('users:login')
                
                login(request, user)
                
                # Başarısız giriş denemelerini sıfırla
                if user.failed_login_attempts > 0:
                    user.failed_login_attempts = 0
                    user.save()
                
                # Log kaydı
                UserLog.log_activity(
                    user=user,
                    log_type='user_login',
                    description='Başarılı giriş',
                    ip_address=get_client_ip(request),
                    user_agent=get_user_agent(request)
                )
                
                messages.success(request, f'Hoş geldiniz, {user.get_full_name()}!')
                return redirect('dashboard:home')
            else:
                # Başarısız giriş denemesi
                try:
                    user = CustomUser.objects.get(username=username)
                    user.failed_login_attempts += 1
                    
                    # 5 başarısız denemeden sonra hesabı kilitle
                    if user.failed_login_attempts >= 5:
                        user.is_locked = True
                        user.locked_at = timezone.now()
                        messages.error(request, 'Çok fazla başarısız giriş denemesi. Hesabınız kilitlendi.')
                    else:
                        messages.error(request, f'Yanlış şifre. Kalan deneme: {5 - user.failed_login_attempts}')
                    
                    user.save()
                    
                    # Log kaydı
                    UserLog.log_activity(
                        user=user,
                        log_type='failed_login',
                        description=f'Başarısız giriş denemesi ({user.failed_login_attempts}/5)',
                        ip_address=get_client_ip(request),
                        user_agent=get_user_agent(request)
                    )
                except CustomUser.DoesNotExist:
                    messages.error(request, 'Geçersiz kullanıcı adı veya şifre.')
        else:
            messages.error(request, 'Geçersiz kullanıcı adı veya şifre.')
    else:
        form = CustomAuthenticationForm()
    
    return render(request, 'users/login.html', {'form': form})

def logout_view(request):
    """Kullanıcı çıkış view'ı"""
    if request.user.is_authenticated:
        # Log kaydı
        UserLog.log_activity(
            user=request.user,
            log_type='user_logout',
            description='Çıkış yapıldı',
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request)
        )
        
        logout(request)
        messages.success(request, 'Başarıyla çıkış yapıldı.')
    
    return redirect('users:login')

@login_required
def profile_view(request):
    """Kullanıcı profil view'ı"""
    if request.method == 'POST':
        # Profil resmi güncelleme
        if 'update_image' in request.POST:
            if 'profile_image' in request.FILES:
                request.user.profile_image = request.FILES['profile_image']
                request.user.save()
                
                # Log kaydı
                UserLog.log_activity(
                    user=request.user,
                    log_type='profile_image_update',
                    description='Profil resmi güncellendi',
                    ip_address=get_client_ip(request),
                    user_agent=get_user_agent(request)
                )
                
                messages.success(request, 'Profil resminiz başarıyla güncellendi.')
                return redirect('users:profile')
            else:
                messages.error(request, 'Lütfen bir resim seçin.')
                return redirect('users:profile')
        
        # Profil bilgileri güncelleme
        elif 'update_profile' in request.POST:
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            email = request.POST.get('email')
            phone = request.POST.get('phone')
            
            if first_name and last_name and email:
                request.user.first_name = first_name
                request.user.last_name = last_name
                request.user.email = email
                request.user.phone = phone
                request.user.save()
                
                # Log kaydı
                UserLog.log_activity(
                    user=request.user,
                    log_type='profile_update',
                    description='Profil bilgileri güncellendi',
                    ip_address=get_client_ip(request),
                    user_agent=get_user_agent(request)
                )
                
                messages.success(request, 'Profil bilgileriniz başarıyla güncellendi.')
                return redirect('users:profile')
            else:
                messages.error(request, 'Lütfen tüm gerekli alanları doldurun.')
    
    # Son aktiviteleri al
    recent_activities = UserLog.objects.filter(user=request.user).order_by('-created_at')[:5]
    
    context = {
        'user': request.user,
        'recent_activities': recent_activities
    }
    return render(request, 'users/profile.html', context)

@login_required
def change_password_view(request):
    """Şifre değiştirme view'ı"""
    if request.method == 'POST':
        form = PasswordChangeForm(request.POST)
        if form.is_valid():
            old_password = form.cleaned_data.get('old_password')
            new_password1 = form.cleaned_data.get('new_password1')
            
            if request.user.check_password(old_password):
                request.user.set_password(new_password1)
                request.user.save()
                
                # Log kaydı
                UserLog.log_activity(
                    user=request.user,
                    log_type='password_change',
                    description='Şifre değiştirildi',
                    ip_address=get_client_ip(request),
                    user_agent=get_user_agent(request)
                )
                
                # Yeni şifre ile oturumu yenile
                update_session_auth_hash(request, request.user)
                messages.success(request, 'Şifreniz başarıyla değiştirildi.')
                return redirect('users:profile')
            else:
                messages.error(request, 'Mevcut şifreniz yanlış.')
    else:
        form = PasswordChangeForm()
    
    return render(request, 'users/change_password.html', {'form': form})

@login_required
def user_list_view(request):
    """Kullanıcı listesi view'ı (sadece admin'ler için)"""
    if not request.user.can_manage_users:
        messages.error(request, 'Bu sayfaya erişim yetkiniz yok.')
        return redirect('dashboard:home')
    
    users = CustomUser.objects.all().order_by('-date_joined')
    
    # Filtreleme
    role_filter = request.GET.get('role')
    if role_filter:
        users = users.filter(role=role_filter)
    
    status_filter = request.GET.get('status')
    if status_filter == 'active':
        users = users.filter(is_active=True)
    elif status_filter == 'inactive':
        users = users.filter(is_active=False)
    elif status_filter == 'locked':
        users = users.filter(is_locked=True)
    
    search_query = request.GET.get('search')
    if search_query:
        users = users.filter(
            username__icontains=search_query
        ) | users.filter(
            first_name__icontains=search_query
        ) | users.filter(
            last_name__icontains=search_query
        ) | users.filter(
            tc_kimlik__icontains=search_query
        )
    
    # Pagination
    paginator = Paginator(users, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # İstatistik verileri
    total_users = CustomUser.objects.count()
    active_users = CustomUser.objects.filter(is_active=True).count()
    admin_users = CustomUser.objects.filter(role='admin').count()
    superadmin_users = CustomUser.objects.filter(role='superadmin').count()
    
    # Bu ay yeni kullanıcılar
    from datetime import datetime, timedelta
    from django.utils import timezone
    current_month = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    new_users_this_month = CustomUser.objects.filter(date_joined__gte=current_month).count()
    
    # Kilitli kullanıcılar
    locked_users = CustomUser.objects.filter(is_locked=True).count()
    
    context = {
        'page_obj': page_obj,
        'users': page_obj,  # Backward compatibility
        'role_choices': CustomUser.ROLE_CHOICES,
        'current_filters': {
            'role': role_filter,
            'status': status_filter,
            'search': search_query
        },
        'total_users': total_users,
        'active_users': active_users,
        'admin_users': admin_users,
        'superadmin_users': superadmin_users,
        'new_users_this_month': new_users_this_month,
        'locked_users': locked_users,
        'is_admin': True
    }
    return render(request, 'users/user_list.html', context)

@login_required
def unlock_user_view(request, user_id):
    """Kullanıcı hesabını açma view'ı (sadece admin'ler için)"""
    if not request.user.can_manage_users:
        messages.error(request, 'Bu işlem için yetkiniz yok.')
        return redirect('users:user_list')
    
    user = get_object_or_404(CustomUser, id=user_id)
    
    if user.is_locked:
        user.unlock_account()
        
        # Log kaydı
        UserLog.log_activity(
            user=user,
            log_type='account_unlocked',
            description=f'Hesap {request.user.get_full_name()} tarafından açıldı',
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request)
        )
        
        messages.success(request, f'{user.get_full_name()} kullanıcısının hesabı açıldı.')
    else:
        messages.info(request, f'{user.get_full_name()} kullanıcısının hesabı zaten açık.')
    
    return redirect('users:user_list')

@login_required
def user_create_view(request):
    """Yeni kullanıcı oluşturma view'ı (sadece admin'ler için)"""
    if not request.user.can_manage_users:
        messages.error(request, 'Bu sayfaya erişim yetkiniz yok.')
        return redirect('users:user_list')
    
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password1'])
            user.save()
            
            # Log kaydı
            UserLog.log_activity(
                user=request.user,
                log_type='user_register',
                description=f'Yeni kullanıcı oluşturuldu: {user.username}',
                ip_address=get_client_ip(request),
                user_agent=get_user_agent(request)
            )
            
            messages.success(request, f'Kullanıcı başarıyla oluşturuldu: {user.username}')
            return redirect('users:user_list')
        else:
            messages.error(request, 'Lütfen form hatalarını düzeltin.')
    else:
        form = CustomUserCreationForm()
    
    context = {
        'form': form,
        'is_admin': True
    }
    return render(request, 'users/user_form.html', context)

@login_required
def edit_user_view(request, user_id):
    """Kullanıcı düzenleme view'ı (sadece admin'ler için)"""
    if not request.user.can_manage_users:
        messages.error(request, 'Bu işlem için yetkiniz yok.')
        return redirect('dashboard:home')
    
    user = get_object_or_404(CustomUser, id=user_id)
    
    if request.method == 'POST':
        form = CustomUserUpdateForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            
            # Log kaydı
            UserLog.log_activity(
                user=request.user,
                log_type='user_updated',
                description=f'Kullanıcı güncellendi: {user.get_full_name()}',
                ip_address=get_client_ip(request),
                user_agent=get_user_agent(request)
            )
            
            messages.success(request, f'{user.get_full_name()} başarıyla güncellendi.')
            return redirect('users:user_list')
    else:
        form = CustomUserUpdateForm(instance=user)
    
    context = {
        'form': form,
        'user': user,
        'action': 'edit',
        'is_admin': True
    }
    return render(request, 'users/user_form.html', context)

@login_required
def delete_user_view(request, user_id):
    """Kullanıcı silme view'ı (sadece admin'ler için)"""
    if not request.user.can_manage_users:
        messages.error(request, 'Bu işlem için yetkiniz yok.')
        return redirect('dashboard:home')
    
    user = get_object_or_404(CustomUser, id=user_id)
    
    # Kendini silmeye çalışıyorsa engelle
    if user == request.user:
        messages.error(request, 'Kendi hesabınızı silemezsiniz.')
        return redirect('users:user_list')
    
    if request.method == 'POST':
        user_name = user.get_full_name()
        user.delete()
        
        # Log kaydı
        UserLog.log_activity(
            user=request.user,
            log_type='user_deleted',
            description=f'Kullanıcı silindi: {user_name}',
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request)
        )
        
        messages.success(request, f'{user_name} başarıyla silindi.')
        return redirect('users:user_list')
    
    context = {
        'user': user,
        'is_admin': True
    }
    return render(request, 'users/user_delete.html', context)

@csrf_exempt
@require_http_methods(["POST"])
def check_tc_kimlik(request):
    """TC Kimlik numarası kontrolü (AJAX)"""
    tc_kimlik = request.POST.get('tc_kimlik')
    if tc_kimlik:
        exists = CustomUser.objects.filter(tc_kimlik=tc_kimlik).exists()
        return JsonResponse({'exists': exists})
    return JsonResponse({'error': 'TC Kimlik numarası gerekli'})

@csrf_exempt
@require_http_methods(["POST"])
def check_email(request):
    """E-posta kontrolü (AJAX)"""
    email = request.POST.get('email')
    if email:
        exists = CustomUser.objects.filter(email=email).exists()
        return JsonResponse({'exists': exists})
    return JsonResponse({'error': 'E-posta adresi gerekli'})

@csrf_exempt
@require_http_methods(["POST"])
def check_username(request):
    """Kullanıcı adı kontrolü (AJAX)"""
    username = request.POST.get('username')
    if username:
        exists = CustomUser.objects.filter(username=username).exists()
        return JsonResponse({'exists': exists})
    return JsonResponse({'error': 'Kullanıcı adı gerekli'})

@login_required
def user_permissions_view(request):
    """Kullanıcı yetki yönetimi view'ı (sadece superadmin'ler için)"""
    if not request.user.role == 'superadmin':
        messages.error(request, 'Bu sayfaya erişim yetkiniz yok. Sadece Süper Admin\'ler kullanıcı yetkilerini düzenleyebilir.')
        return redirect('dashboard:home')
    
    # Kullanıcı seçimi
    selected_user_id = request.GET.get('user_id')
    selected_user = None
    
    if selected_user_id:
        try:
            selected_user = get_object_or_404(CustomUser, id=selected_user_id)
        except (ValueError, CustomUser.DoesNotExist):
            messages.error(request, 'Geçersiz kullanıcı ID\'si.')
            selected_user = None
    
    # Tüm kullanıcıları getir
    users = CustomUser.objects.all().order_by('-date_joined')
    
    # İstatistikler
    total_users = users.count()
    active_users = users.filter(is_active=True).count()
    admin_users = users.filter(role='admin').count()
    superadmin_users = users.filter(role='superadmin').count()
    
    # Filtreleme
    role_filter = request.GET.get('role')
    status_filter = request.GET.get('status')
    search_query = request.GET.get('search')
    
    if role_filter:
        users = users.filter(role=role_filter)
    
    if status_filter == 'active':
        users = users.filter(is_active=True)
    elif status_filter == 'inactive':
        users = users.filter(is_active=False)
    elif status_filter == 'locked':
        users = users.filter(is_locked=True)
    
    if search_query:
        users = users.filter(
            Q(username__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(tc_kimlik__icontains=search_query) |
            Q(email__icontains=search_query)
        )
    
    # Sayfalama
    paginator = Paginator(users, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Rol seçenekleri
    role_choices = CustomUser.ROLE_CHOICES
    
    context = {
        'users': users,  # Tüm kullanıcılar (tablo için)
        'page_obj': page_obj,  # Sayfalanmış kullanıcılar
        'selected_user': selected_user,  # Seçilen kullanıcı
        'total_users': total_users,
        'active_users': active_users,
        'admin_users': admin_users,
        'superadmin_users': superadmin_users,
        'role_choices': role_choices,
        'current_filters': {
            'role': role_filter,
            'status': status_filter,
            'search': search_query
        }
    }
    
    return render(request, 'users/user_permissions.html', context)

@login_required
def update_user_permissions_view(request, user_id):
    """Kullanıcı yetkilerini düzenleme view'ı (sadece Super Admin için)"""
    if request.user.role != 'superadmin':
        messages.error(request, 'Bu işlem için yetkiniz yok.')
        return redirect('users:user_permissions')
    
    try:
        target_user = get_object_or_404(CustomUser, id=user_id)
    except CustomUser.DoesNotExist:
        messages.error(request, 'Kullanıcı bulunamadı.')
        return redirect('users:user_permissions')
    
    if request.method == 'POST':
        # Form verilerini al
        new_role = request.POST.get('role')
        is_active = request.POST.get('is_active') == 'on'
        is_staff = request.POST.get('is_staff') == 'on'
        is_superuser = request.POST.get('is_superuser') == 'on'
        
        # Değişiklikleri kaydet
        old_role = target_user.role
        old_is_active = target_user.is_active
        old_is_staff = target_user.is_staff
        old_is_superuser = target_user.is_superuser
        
        target_user.role = new_role
        target_user.is_active = is_active
        target_user.is_staff = is_staff
        target_user.is_superuser = is_superuser
        
        # Hesap kilidini kaldır (eğer aktif yapılıyorsa)
        if is_active and target_user.is_locked:
            target_user.is_locked = False
        
        target_user.save()
        
        # Değişiklik loglarını kaydet
        changes = []
        if old_role != new_role:
            changes.append(f"Rol: {old_role} → {new_role}")
        if old_is_active != is_active:
            changes.append(f"Aktif: {old_is_active} → {is_active}")
        if old_is_staff != is_staff:
            changes.append(f"Staff: {old_is_staff} → {is_staff}")
        if old_is_superuser != is_superuser:
            changes.append(f"Superuser: {old_is_superuser} → {is_superuser}")
        
        if changes:
            change_description = f"Yetki güncellendi: {', '.join(changes)}"
            
            # Log kaydı - log_type'ı 20 karakter ile sınırla
            UserLog.log_activity(
                user=request.user,
                log_type='permission_update',  # 20 karakter altında
                description=change_description,
                ip_address=get_client_ip(request),
                user_agent=get_user_agent(request)
            )
            
            messages.success(request, f'✅ {target_user.get_full_name()} kullanıcısının yetkileri başarıyla güncellendi!')
        else:
            messages.info(request, 'ℹ️ Herhangi bir değişiklik yapılmadı.')
        
        return redirect('users:user_permissions')
    
    context = {
        'target_user': target_user,
        'role_choices': CustomUser.ROLE_CHOICES,
        'is_admin': True
    }
    
    return render(request, 'users/user_permissions_edit.html', context)

@login_required
def bulk_update_permissions_view(request):
    """Toplu yetki güncelleme view'ı (sadece superadmin'ler için)"""
    if not request.user.role == 'superadmin':
        messages.error(request, 'Bu işlem için yetkiniz yok.')
        return redirect('users:user_permissions')
    
    if request.method == 'POST':
        user_ids = request.POST.getlist('user_ids')
        new_role = request.POST.get('new_role')
        new_status = request.POST.get('new_status')
        
        if not user_ids:
            messages.error(request, 'Lütfen en az bir kullanıcı seçin.')
            return redirect('users:user_permissions')
        
        if not new_role and not new_status:
            messages.error(request, 'Lütfen güncellenecek alanları seçin.')
            return redirect('users:user_permissions')
        
        updated_count = 0
        
        for user_id in user_ids:
            try:
                user = CustomUser.objects.get(id=user_id)
                
                # Kendini düşük yetkiye düşürmeye çalışıyorsa atla
                if user == request.user and new_role and new_role != 'superadmin':
                    continue
                
                if new_role:
                    user.role = new_role
                
                if new_status:
                    user.is_active = (new_status == 'active')
                    if new_status == 'active':
                        user.is_locked = False
                        user.locked_at = None
                        user.failed_login_attempts = 0
                
                user.save()
                updated_count += 1
                
            except CustomUser.DoesNotExist:
                continue
        
        if updated_count > 0:
            messages.success(request, f'{updated_count} kullanıcının yetkileri başarıyla güncellendi.')
        else:
            messages.warning(request, 'Güncellenebilecek kullanıcı bulunamadı.')
        
        return redirect('users:user_permissions')
    
    return redirect('users:user_permissions')

@login_required
def quick_actions_view(request):
    """Hızlı işlemler yönetimi view'ı"""
    if request.method == 'POST':
        action = request.POST.get('action')
        display_name = request.POST.get('display_name')
        icon = request.POST.get('icon')
        color = request.POST.get('color')
        
        if action and display_name:
            # Mevcut hızlı işlemi güncelle veya yeni oluştur
            quick_action, created = QuickAction.objects.get_or_create(
                user=request.user,
                action=action,
                defaults={
                    'display_name': display_name,
                    'icon': icon or 'fas fa-star',
                    'color': color or 'cyan',
                    'order': QuickAction.objects.filter(user=request.user).count()
                }
            )
            
            if not created:
                quick_action.display_name = display_name
                quick_action.icon = icon or quick_action.icon
                quick_action.color = color or quick_action.color
                quick_action.save()
            
            messages.success(request, f'✅ Hızlı işlem eklendi: {display_name}')
            return redirect('users:quick_actions')
    
    # Kullanıcının mevcut hızlı işlemleri
    user_quick_actions = QuickAction.objects.filter(user=request.user, is_active=True).order_by('order')
    
    # Mevcut olmayan işlemler
    existing_actions = set(user_quick_actions.values_list('action', flat=True))
    available_actions = [choice for choice in QuickAction.ACTION_CHOICES if choice[0] not in existing_actions]
    
    context = {
        'user_quick_actions': user_quick_actions,
        'available_actions': available_actions,
        'color_choices': [
            ('cyan', 'Cyan'),
            ('blue', 'Mavi'),
            ('green', 'Yeşil'),
            ('yellow', 'Sarı'),
            ('red', 'Kırmızı'),
            ('purple', 'Mor'),
            ('pink', 'Pembe'),
            ('indigo', 'İndigo'),
        ],
        'is_admin': True
    }
    
    return render(request, 'users/quick_actions.html', context)

@login_required
def quick_action_delete_view(request, action_id):
    """Hızlı işlem silme view'ı"""
    try:
        quick_action = QuickAction.objects.get(id=action_id, user=request.user)
        action_name = quick_action.display_name
        quick_action.delete()
        messages.success(request, f'✅ Hızlı işlem silindi: {action_name}')
    except QuickAction.DoesNotExist:
        messages.error(request, '❌ Hızlı işlem bulunamadı.')
    
    return redirect('users:quick_actions')

@login_required
def quick_action_reorder_view(request):
    """Hızlı işlem sıralama view'ı (AJAX)"""
    if request.method == 'POST':
        action_ids = request.POST.getlist('action_ids[]')
        
        for index, action_id in enumerate(action_ids):
            try:
                quick_action = QuickAction.objects.get(id=action_id, user=request.user)
                quick_action.order = index
                quick_action.save()
            except QuickAction.DoesNotExist:
                continue
        
        return JsonResponse({'success': True})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})
