from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from devices.models import Device
from users.models import UserLog
import datetime

User = get_user_model()

class DashboardViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            tc_kimlik='12345678901'
        )
        
        # Test cihazları oluştur
        self.device1 = Device.objects.create(
            user=self.user,
            gsm_number='+905551234567',
            device_email='phone@example.com',
            device_type='phone',
            device_name='Test Phone'
        )
        
        self.device2 = Device.objects.create(
            user=self.user,
            gsm_number='+905559876543',
            device_email='tablet@example.com',
            device_type='tablet',
            device_name='Test Tablet'
        )
        
        # Test log kayıtları oluştur
        self.log1 = UserLog.objects.create(
            user=self.user,
            log_type='login',
            description='Test login',
            ip_address='127.0.0.1'
        )
        
        self.log2 = UserLog.objects.create(
            user=self.user,
            log_type='device_add',
            description='Test device added',
            ip_address='127.0.0.1'
        )
    
    def test_home_view_authenticated(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('dashboard:home'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'dashboard/home.html')
    
    def test_home_view_unauthenticated(self):
        response = self.client.get(reverse('dashboard:home'))
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    def test_home_view_context_data(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('dashboard:home'))
        
        # Context'te gerekli veriler olmalı
        self.assertIn('total_devices', response.context)
        self.assertIn('active_devices', response.context)
        self.assertIn('recent_activities', response.context)
        
        # Toplam cihaz sayısı doğru olmalı
        self.assertEqual(response.context['total_devices'], 2)
        self.assertEqual(response.context['active_devices'], 2)
    
    def test_statistics_view_authenticated(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('dashboard:statistics'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'dashboard/statistics.html')
    
    def test_statistics_view_unauthenticated(self):
        response = self.client.get(reverse('dashboard:statistics'))
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    def test_statistics_view_context_data(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('dashboard:statistics'))
        
        # Context'te gerekli veriler olmalı
        self.assertIn('device_stats', response.context)
        self.assertIn('user_stats', response.context)
        self.assertIn('activity_stats', response.context)
    
    def test_activity_log_view_authenticated(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('dashboard:activity_log'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'dashboard/activity_log.html')
    
    def test_activity_log_view_unauthenticated(self):
        response = self.client.get(reverse('dashboard:activity_log'))
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    def test_activity_log_view_context_data(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('dashboard:activity_log'))
        
        # Context'te gerekli veriler olmalı
        self.assertIn('activities', response.context)
        self.assertIn('filter_form', response.context)
        
        # Aktiviteler listelenmeli
        activities = response.context['activities']
        self.assertEqual(len(activities), 2)
    
    def test_system_info_view_authenticated(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('dashboard:system_info'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'dashboard/system_info.html')
    
    def test_system_info_view_unauthenticated(self):
        response = self.client.get(reverse('dashboard:system_info'))
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    def test_system_info_view_context_data(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('dashboard:system_info'))
        
        # Context'te gerekli veriler olmalı
        self.assertIn('system_info', response.context)
        self.assertIn('database_info', response.context)
        self.assertIn('django_info', response.context)
    
    def test_admin_panel_view_superuser(self):
        # Superuser oluştur
        superuser = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass123',
            tc_kimlik='98765432109'
        )
        
        self.client.login(username='admin', password='adminpass123')
        response = self.client.get(reverse('dashboard:admin_panel'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'dashboard/admin_panel.html')
    
    def test_admin_panel_view_regular_user(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('dashboard:admin_panel'))
        self.assertEqual(response.status_code, 403)  # Permission denied
    
    def test_admin_panel_view_unauthenticated(self):
        response = self.client.get(reverse('dashboard:admin_panel'))
        self.assertEqual(response.status_code, 302)  # Redirect to login

class DashboardContextTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            tc_kimlik='12345678901'
        )
    
    def test_home_view_empty_context(self):
        """Boş veri ile home view test edilmeli"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('dashboard:home'))
        
        # Boş veri durumunda context değerleri
        self.assertEqual(response.context['total_devices'], 0)
        self.assertEqual(response.context['active_devices'], 0)
        self.assertEqual(len(response.context['recent_activities']), 0)
    
    def test_statistics_view_empty_context(self):
        """Boş veri ile statistics view test edilmeli"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('dashboard:statistics'))
        
        # Boş veri durumunda context değerleri
        self.assertIn('device_stats', response.context)
        self.assertIn('user_stats', response.context)
        self.assertIn('activity_stats', response.context)

class DashboardURLTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            tc_kimlik='12345678901'
        )
    
    def test_dashboard_urls_exist(self):
        """Dashboard URL'lerinin var olduğu test edilmeli"""
        self.client.login(username='testuser', password='testpass123')
        
        urls_to_test = [
            'dashboard:home',
            'dashboard:statistics',
            'dashboard:activity_log',
            'dashboard:system_info',
        ]
        
        for url_name in urls_to_test:
            try:
                response = self.client.get(reverse(url_name))
                # URL var olmalı (200, 302, 403 gibi status kodları)
                self.assertIn(response.status_code, [200, 302, 403])
            except Exception as e:
                self.fail(f"URL {url_name} bulunamadı: {e}")
    
    def test_admin_panel_url_superuser(self):
        """Admin panel URL'inin superuser için erişilebilir olduğu test edilmeli"""
        superuser = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass123',
            tc_kimlik='98765432109'
        )
        
        self.client.login(username='admin', password='adminpass123')
        response = self.client.get(reverse('dashboard:admin_panel'))
        self.assertEqual(response.status_code, 200)
