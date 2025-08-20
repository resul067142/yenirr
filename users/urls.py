from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    # Kimlik doğrulama
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    
    # Profil yönetimi
    path('profile/', views.profile_view, name='profile'),
    path('change-password/', views.change_password_view, name='change_password'),
    
    # Kullanıcı yönetimi (admin'ler için)
    path('list/', views.user_list_view, name='user_list'),
    path('unlock/<int:user_id>/', views.unlock_user_view, name='unlock_user'),
    path('add/', views.add_user_view, name='add_user'),
    path('edit/<int:user_id>/', views.edit_user_view, name='edit_user'),
    path('delete/<int:user_id>/', views.delete_user_view, name='delete_user'),
    
    # AJAX kontrolleri
    path('check-tc-kimlik/', views.check_tc_kimlik, name='check_tc_kimlik'),
    path('check-email/', views.check_email, name='check_email'),
    path('check-username/', views.check_username, name='check_username'),
]
