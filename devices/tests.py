from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import Device
from .forms import DeviceForm
import datetime

User = get_user_model()

class DeviceModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            tc_kimlik='12345678901'
        )
        
        self.device_data = {
            'user': self.user,
            'gsm_number': '+905551234567',
            'device_email': 'device@example.com',
            'device_type': 'phone',
            'device_name': 'Test Phone',
            'brand': 'Test Brand',
            'model': 'Test Model',
            'imei': '123456789012345',
            'is_active': True
        }
    
    def test_create_device(self):
        device = Device.objects.create(**self.device_data)
        self.assertEqual(device.user, self.user)
        self.assertEqual(device.gsm_number, '+905551234567')
        self.assertEqual(device.device_email, 'device@example.com')
        self.assertEqual(device.device_type, 'phone')
        self.assertEqual(device.device_name, 'Test Phone')
        self.assertTrue(device.is_active)
        self.assertIsNotNone(device.created_at)
    
    def test_device_str_representation(self):
        device = Device.objects.create(**self.device_data)
        expected_str = f"{device.device_name} - {device.gsm_number} ({device.user.get_full_name()})"
        self.assertEqual(str(device), expected_str)
    
    def test_device_meta_ordering(self):
        device1 = Device.objects.create(**self.device_data)
        device2_data = self.device_data.copy()
        device2_data['device_email'] = 'device2@example.com'
        device2_data['gsm_number'] = '+905559876543'
        device2 = Device.objects.create(**device2_data)
        
        devices = Device.objects.all()
        # En son oluşturulan cihaz ilk sırada olmalı
        self.assertEqual(devices[0], device2)
        self.assertEqual(devices[1], device1)
    
    def test_device_type_choices(self):
        device_types = [choice[0] for choice in Device.DEVICE_TYPE_CHOICES]
        expected_types = ['phone', 'tablet', 'computer', 'iot', 'vehicle_camera', 
                         'vehicle_tracker', 'ip_camera', 'other']
        self.assertEqual(device_types, expected_types)
    
    def test_device_group_field(self):
        device = Device.objects.create(
            **self.device_data,
            device_group='Test Group'
        )
        self.assertEqual(device.device_group, 'Test Group')

class DeviceFormTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            tc_kimlik='12345678901'
        )
    
    def test_device_form_valid(self):
        form_data = {
            'gsm_number': '+905551234567',
            'device_email': 'device@example.com',
            'device_type': 'phone',
            'device_name': 'Test Phone',
            'brand': 'Test Brand',
            'model': 'Test Model',
            'imei': '123456789012345'
        }
        
        form = DeviceForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_device_form_invalid_gsm(self):
        form_data = {
            'gsm_number': 'invalid',
            'device_email': 'device@example.com',
            'device_type': 'phone'
        }
        
        form = DeviceForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('gsm_number', form.errors)
    
    def test_device_form_invalid_email(self):
        form_data = {
            'gsm_number': '+905551234567',
            'device_email': 'invalid-email',
            'device_type': 'phone'
        }
        
        form = DeviceForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('device_email', form.errors)
    
    def test_device_form_missing_required_fields(self):
        form_data = {
            'device_name': 'Test Phone'
        }
        
        form = DeviceForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('gsm_number', form.errors)
        self.assertIn('device_email', form.errors)
        self.assertIn('device_type', form.errors)

class DeviceViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            tc_kimlik='12345678901'
        )
        
        self.device = Device.objects.create(
            user=self.user,
            gsm_number='+905551234567',
            device_email='device@example.com',
            device_type='phone',
            device_name='Test Phone'
        )
    
    def test_device_list_view_authenticated(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('devices:device_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'devices/device_list.html')
        self.assertContains(response, 'Test Phone')
    
    def test_device_list_view_unauthenticated(self):
        response = self.client.get(reverse('devices:device_list'))
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    def test_device_detail_view_authenticated(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('devices:device_detail', args=[self.device.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'devices/device_detail.html')
        self.assertContains(response, 'Test Phone')
    
    def test_device_detail_view_unauthenticated(self):
        response = self.client.get(reverse('devices:device_detail', args=[self.device.id]))
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    def test_device_add_view_authenticated(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('devices:device_add'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'devices/device_form.html')
    
    def test_device_add_view_unauthenticated(self):
        response = self.client.get(reverse('devices:device_add'))
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    def test_device_add_success(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(reverse('devices:device_add'), {
            'gsm_number': '+905559876543',
            'device_email': 'newdevice@example.com',
            'device_type': 'tablet',
            'device_name': 'New Tablet',
            'brand': 'New Brand',
            'model': 'New Model'
        })
        self.assertEqual(response.status_code, 302)  # Redirect after creation
        self.assertTrue(Device.objects.filter(device_email='newdevice@example.com').exists())
    
    def test_device_edit_view_authenticated(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('devices:device_edit', args=[self.device.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'devices/device_form.html')
    
    def test_device_edit_success(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(reverse('devices:device_edit', args=[self.device.id]), {
            'gsm_number': '+905551234567',
            'device_email': 'device@example.com',
            'device_type': 'phone',
            'device_name': 'Updated Phone',
            'brand': 'Updated Brand',
            'model': 'Updated Model'
        })
        self.assertEqual(response.status_code, 302)  # Redirect after update
        self.device.refresh_from_db()
        self.assertEqual(self.device.device_name, 'Updated Phone')
    
    def test_device_delete_view_authenticated(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('devices:device_delete', args=[self.device.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'devices/device_delete.html')
    
    def test_device_delete_success(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(reverse('devices:device_delete', args=[self.device.id]))
        self.assertEqual(response.status_code, 302)  # Redirect after deletion
        self.assertFalse(Device.objects.filter(id=self.device.id).exists())

class DeviceStatisticsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            tc_kimlik='12345678901'
        )
        
        # Test cihazları oluştur
        Device.objects.create(
            user=self.user,
            gsm_number='+905551234567',
            device_email='phone@example.com',
            device_type='phone',
            device_name='Test Phone'
        )
        
        Device.objects.create(
            user=self.user,
            gsm_number='+905559876543',
            device_email='tablet@example.com',
            device_type='tablet',
            device_name='Test Tablet'
        )
    
    def test_device_statistics_view_authenticated(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('devices:device_statistics'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'devices/device_statistics.html')
    
    def test_device_statistics_view_unauthenticated(self):
        response = self.client.get(reverse('devices:device_statistics'))
        self.assertEqual(response.status_code, 302)  # Redirect to login
