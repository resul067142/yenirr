from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    # Ana dashboard
    path('', views.home_view, name='home'),
    
    # İstatistikler ve raporlar
    path('statistics/', views.statistics_view, name='statistics'),
    path('activity-log/', views.activity_log_view, name='activity_log'),
    path('system-info/', views.system_info_view, name='system_info'),
]
