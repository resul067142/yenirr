from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.core.paginator import Paginator
from django.db import transaction
from .models import CustomUser, UserLog
from .forms import CustomUserCreationForm, CustomUserUpdateForm, CustomAuthenticationForm, PasswordChangeForm
from django.utils import timezone

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
    
    context = {
        'user': request.user
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
    if not request.user.can_manage_users():
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
    
    context = {
        'users': page_obj,
        'role_choices': CustomUser.ROLE_CHOICES,
        'current_filters': {
            'role': role_filter,
            'status': status_filter,
            'search': search_query
        }
    }
    return render(request, 'users/user_list.html', context)

@login_required
def unlock_user_view(request, user_id):
    """Kullanıcı hesabını açma view'ı (sadece admin'ler için)"""
    if not request.user.can_manage_users():
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
def add_user_view(request):
    """Yeni kullanıcı ekleme view'ı (sadece admin'ler için)"""
    if not request.user.can_manage_users():
        messages.error(request, 'Bu işlem için yetkiniz yok.')
        return redirect('dashboard:home')
    
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password1'])
            user.save()
            
            # Log kaydı
            UserLog.log_activity(
                user=request.user,
                log_type='user_created',
                description=f'Yeni kullanıcı oluşturuldu: {user.get_full_name()}',
                ip_address=get_client_ip(request),
                user_agent=get_user_agent(request)
            )
            
            messages.success(request, f'{user.get_full_name()} başarıyla oluşturuldu.')
            return redirect('users:user_list')
    else:
        form = CustomUserCreationForm()
    
    context = {
        'form': form,
        'title': 'Yeni Kullanıcı Ekle'
    }
    return render(request, 'users/user_form.html', context)

@login_required
def edit_user_view(request, user_id):
    """Kullanıcı düzenleme view'ı (sadece admin'ler için)"""
    if not request.user.can_manage_users():
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
        'title': 'Kullanıcı Düzenle'
    }
    return render(request, 'users/user_form.html', context)

@login_required
def delete_user_view(request, user_id):
    """Kullanıcı silme view'ı (sadece admin'ler için)"""
    if not request.user.can_manage_users():
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
        'user': user
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
