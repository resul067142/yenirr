from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.home_view, name='home'),
    path('statistics/', views.statistics_view, name='statistics'),
    path('activity-log/', views.activity_log_view, name='activity_log'),
    path('system-info/', views.system_info_view, name='system_info'),
    path('admin-panel/', views.admin_panel_view, name='admin_panel'),
    
    # API endpoints
    path('api/logs/<int:log_id>/', views.log_detail_api, name='log_detail_api'),
    path('api/logs/<int:log_id>/delete/', views.log_delete_api, name='log_delete_api'),
]
