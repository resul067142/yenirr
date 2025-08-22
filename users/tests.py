from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from .models import CustomUser, UserLog, QuickAction
import tempfile
import os

User = get_user_model()

class CustomUserModelTest(TestCase):
    def setUp(self):
        self.user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpass123',
            'first_name': 'Test',
            'last_name': 'User',
            'tc_kimlik': '12345678901',
            'phone': '+905551234567',
            'role': 'user'
        }
    
    def test_create_user(self):
        user = User.objects.create_user(**self.user_data)
        self.assertEqual(user.username, 'testuser')
        self.assertEqual(user.email, 'test@example.com')
        self.assertEqual(user.tc_kimlik, '12345678901')
        self.assertEqual(user.role, 'user')
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_locked)
    
    def test_create_superuser(self):
        superuser = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass123',
            tc_kimlik='98765432109'
        )
        self.assertTrue(superuser.is_superuser)
        self.assertTrue(superuser.is_staff)
    
    def test_tc_kimlik_validation(self):
        # Geçersiz TC kimlik - model seviyesinde validasyon yok, sadece form seviyesinde
        invalid_user_data = self.user_data.copy()
        invalid_user_data['tc_kimlik'] = '123'
        
        # Model seviyesinde validasyon olmadığı için hata fırlatılmamalı
        user = User.objects.create_user(**invalid_user_data)
        self.assertEqual(user.tc_kimlik, '123')
    
    def test_phone_validation(self):
        # Geçersiz telefon
        invalid_user_data = self.user_data.copy()
        invalid_user_data['phone'] = 'invalid'
        
        user = User.objects.create_user(**invalid_user_data)
        # Telefon validasyonu model seviyesinde yapılmıyor, sadece form seviyesinde
        self.assertEqual(user.phone, 'invalid')

class UserLogModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            tc_kimlik='12345678901'
        )
    
    def test_create_user_log(self):
        log = UserLog.objects.create(
            user=self.user,
            log_type='login',
            description='Test login',
            ip_address='127.0.0.1'
        )
        self.assertEqual(log.user, self.user)
        self.assertEqual(log.log_type, 'login')
        self.assertEqual(log.description, 'Test login')

class QuickActionModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            tc_kimlik='12345678901'
        )
    
    def test_create_quick_action(self):
        action = QuickAction.objects.create(
            user=self.user,
            action='device_add',
            display_name='Test Action',
            icon='fas fa-star',
            color='cyan',
            order=1
        )
        self.assertEqual(action.user, self.user)
        self.assertEqual(action.action, 'device_add')
        self.assertEqual(action.display_name, 'Test Action')

class UserViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            tc_kimlik='12345678901'
        )
    
    def test_login_view(self):
        response = self.client.get(reverse('users:login'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/login.html')
    
    def test_login_success(self):
        response = self.client.post(reverse('users:login'), {
            'username': 'testuser',
            'password': 'testpass123'
        })
        self.assertEqual(response.status_code, 302)  # Redirect after login
    
    def test_login_failure(self):
        response = self.client.post(reverse('users:login'), {
            'username': 'testuser',
            'password': 'wrongpass'
        })
        self.assertEqual(response.status_code, 200)  # Stay on login page
    
    def test_logout_view(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('users:logout'))
        self.assertEqual(response.status_code, 302)  # Redirect after logout
    
    def test_profile_view_authenticated(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('users:profile'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/profile.html')
    
    def test_profile_view_unauthenticated(self):
        response = self.client.get(reverse('users:profile'))
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    def test_register_view(self):
        response = self.client.get(reverse('users:register'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/register.html')
    
    def test_register_success(self):
        response = self.client.post(reverse('users:register'), {
            'username': 'newuser',
            'email': 'new@example.com',
            'password1': 'newpass123',
            'password2': 'newpass123',
            'first_name': 'New',
            'last_name': 'User',
            'tc_kimlik': '11111111111',
            'phone': '+905559876543'
        })
        self.assertEqual(response.status_code, 302)  # Redirect after registration
        self.assertTrue(User.objects.filter(username='newuser').exists())

class UserFormsTest(TestCase):
    def test_user_registration_form(self):
        from .forms import CustomUserCreationForm
        
        form_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password1': 'testpass123',
            'password2': 'testpass123',
            'first_name': 'Test',
            'last_name': 'User',
            'tc_kimlik': '12345678901',
            'phone': '+905551234567'
        }
        
        form = CustomUserCreationForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_user_update_form(self):
        from .forms import CustomUserUpdateForm
        
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            tc_kimlik='12345678901'
        )
        
        form_data = {
            'email': 'newemail@example.com',
            'first_name': 'Updated',
            'last_name': 'User',
            'phone': '+905559876543'
        }
        
        form = CustomUserUpdateForm(data=form_data, instance=user)
        self.assertTrue(form.is_valid())
