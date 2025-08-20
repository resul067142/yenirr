from django.urls import path
from . import views

app_name = 'devices'

urlpatterns = [
    # Cihaz listeleme ve yönetimi
    path('', views.device_list_view, name='device_list'),
    path('add/', views.device_add_view, name='device_add'),
    path('edit/<int:device_id>/', views.device_edit_view, name='device_edit'),
    path('delete/<int:device_id>/', views.device_delete_view, name='device_delete'),
    path('detail/<int:device_id>/', views.device_detail_view, name='device_detail'),
    
    # İstatistikler
    path('statistics/', views.device_statistics_view, name='device_statistics'),
    
    # Export işlemleri
    path('export/csv/', views.device_export_csv, name='device_export_csv'),
    path('export/json/', views.device_export_json, name='device_export_json'),
    
    # AJAX işlemleri
    path('toggle-status/<int:device_id>/', views.device_toggle_status, name='device_toggle_status'),
]
