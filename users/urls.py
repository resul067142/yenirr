from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    # Authentication
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    
    # Profile
    path('profile/', views.profile_view, name='profile'),
    path('change-password/', views.change_password_view, name='change_password'),
    
    # User Management (Admin)
    path('list/', views.user_list_view, name='user_list'),
    path('add/', views.user_create_view, name='add_user'),
    path('edit/<int:user_id>/', views.edit_user_view, name='edit_user'),
    path('delete/<int:user_id>/', views.delete_user_view, name='delete_user'),
    path('unlock/<int:user_id>/', views.unlock_user_view, name='unlock_user'),
    
    # Permissions Management
    path('permissions/', views.user_permissions_view, name='user_permissions'),
    path('permissions/<int:user_id>/edit/', views.update_user_permissions_view, name='update_user_permissions'),
    path('permissions/bulk-update/', views.bulk_update_permissions_view, name='bulk_update_permissions'),
    
    # Quick Actions
    path('quick-actions/', views.quick_actions_view, name='quick_actions'),
    path('quick-actions/<int:action_id>/delete/', views.quick_action_delete_view, name='quick_action_delete'),
    path('quick-actions/reorder/', views.quick_action_reorder_view, name='quick_action_reorder'),
    
    # AJAX checks
    path('check-username/', views.check_username, name='check_username'),
    path('check-email/', views.check_email, name='check_email'),
    path('check-tc-kimlik/', views.check_tc_kimlik, name='check_tc_kimlik'),
]
