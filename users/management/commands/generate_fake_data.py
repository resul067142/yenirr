from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from faker import Faker
from users.models import UserLog, QuickAction
from devices.models import Device
import random
from datetime import timedelta

User = get_user_model()
fake = Faker(['tr_TR'])

class Command(BaseCommand):
    help = 'Generate fake data for testing purposes'

    def add_arguments(self, parser):
        parser.add_argument(
            '--users',
            type=int,
            default=10,
            help='Number of users to create'
        )
        parser.add_argument(
            '--devices',
            type=int,
            default=15,
            help='Number of devices to create per user'
        )
        parser.add_argument(
            '--logs',
            type=int,
            default=15,
            help='Number of user logs to create per user'
        )
        parser.add_argument(
            '--actions',
            type=int,
            default=15,
            help='Number of quick actions to create per user'
        )

    def handle(self, *args, **options):
        self.stdout.write('Starting to generate fake data...')
        
        # Kullanıcı rolleri
        roles = ['superadmin', 'admin', 'user']
        
        # Cihaz türleri
        device_types = ['phone', 'tablet', 'computer', 'iot', 'vehicle_camera', 
                       'vehicle_tracker', 'ip_camera', 'other']
        
        # Marka ve modeller
        brands = ['Samsung', 'Apple', 'Huawei', 'Xiaomi', 'Oppo', 'Vivo', 'OnePlus', 
                 'Sony', 'LG', 'Nokia', 'Motorola', 'Lenovo', 'Dell', 'HP', 'Asus']
        
        models = ['Galaxy S23', 'iPhone 15', 'P40 Pro', 'Redmi Note 12', 'Reno 8', 
                 'X90 Pro', '9 Pro', 'Xperia 1 V', 'G8', '8.3', 'Edge 40', 
                 'ThinkPad', 'Latitude', 'EliteBook', 'ZenBook']
        
        # Log türleri
        log_types = ['login', 'logout', 'device_add', 'device_update', 'device_delete', 
                    'user_add', 'user_update', 'user_delete', 'password_change', 
                    'profile_update', 'export_data', 'import_data', 'bulk_action', 
                    'permission_change', 'system_access']
        
        # Quick action türleri
        action_types = ['device_add', 'device_list', 'user_add', 'user_list', 
                       'statistics', 'activity_log', 'system_info', 'admin_panel', 
                       'profile', 'change_password', 'export_csv', 'export_json', 
                       'bulk_actions', 'permissions']
        
        # Renkler
        colors = ['cyan', 'blue', 'green', 'yellow', 'red', 'purple', 'pink', 'indigo']
        
        # İkonlar
        icons = ['fas fa-mobile-alt', 'fas fa-tablet-alt', 'fas fa-laptop', 
                'fas fa-microchip', 'fas fa-video', 'fas fa-satellite-dish', 
                'fas fa-camera', 'fas fa-cog', 'fas fa-user', 'fas fa-users', 
                'fas fa-chart-bar', 'fas fa-list', 'fas fa-info-circle', 
                'fas fa-shield-alt', 'fas fa-key']
        
        # 10 farklı kullanıcı oluştur
        users_created = 0
        for i in range(options['users']):
            try:
                # Kullanıcı verileri
                username = fake.user_name()
                email = fake.email()
                first_name = fake.first_name()
                last_name = fake.last_name()
                tc_kimlik = fake.numerify(text='###########')  # 11 haneli
                phone = fake.numerify(text='+90##########')  # Türkiye formatı
                role = random.choice(roles)
                
                # Kullanıcı oluştur
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password='testpass123',
                    first_name=first_name,
                    last_name=last_name,
                    tc_kimlik=tc_kimlik,
                    phone=phone,
                    role=role
                )
                
                # Superadmin ve admin kullanıcıları staff yap
                if role in ['superadmin', 'admin']:
                    user.is_staff = True
                    user.save()
                
                # Superadmin kullanıcısı superuser yap
                if role == 'superadmin':
                    user.is_superuser = True
                    user.save()
                
                users_created += 1
                self.stdout.write(f'Created user: {username} ({role})')
                
                # Her kullanıcı için 15 cihaz oluştur
                devices_created = 0
                for j in range(options['devices']):
                    try:
                        device_type = random.choice(device_types)
                        brand = random.choice(brands)
                        model = random.choice(models)
                        gsm_number = fake.numerify(text='+90##########')
                        device_email = f"{username}{j+1}@device.com"
                        device_name = f"{brand} {model} - {username}"
                        
                        device = Device.objects.create(
                            user=user,
                            gsm_number=gsm_number,
                            device_email=device_email,
                            device_type=device_type,
                            device_name=device_name,
                            brand=brand,
                            model=model,
                            imei=fake.numerify(text='###############'),
                            is_active=random.choice([True, True, True, False]),  # %75 aktif
                            device_group=random.choice(['İş', 'Kişisel', 'Test', 'Demo', 'Backup', None]),
                            notes=fake.text(max_nb_chars=200)
                        )
                        devices_created += 1
                    except Exception as e:
                        self.stdout.write(f'Error creating device: {e}')
                
                self.stdout.write(f'  Created {devices_created} devices for {username}')
                
                # Her kullanıcı için 15 log kaydı oluştur
                logs_created = 0
                for j in range(options['logs']):
                    try:
                        log_type = random.choice(log_types)
                        description = fake.sentence()
                        ip_address = fake.ipv4()
                        user_agent = fake.user_agent()
                        
                        # Son 30 gün içinde rastgele tarih
                        created_at = timezone.now() - timedelta(
                            days=random.randint(0, 30),
                            hours=random.randint(0, 23),
                            minutes=random.randint(0, 59)
                        )
                        
                        log = UserLog.objects.create(
                            user=user,
                            log_type=log_type,
                            description=description,
                            ip_address=ip_address,
                            user_agent=user_agent,
                            created_at=created_at
                        )
                        logs_created += 1
                    except Exception as e:
                        self.stdout.write(f'Error creating log: {e}')
                
                self.stdout.write(f'  Created {logs_created} logs for {username}')
                
                # Her kullanıcı için 15 quick action oluştur
                actions_created = 0
                for j in range(options['actions']):
                    try:
                        action = random.choice(action_types)
                        display_name = fake.word().title()
                        icon = random.choice(icons)
                        color = random.choice(colors)
                        order = j + 1
                        
                        quick_action = QuickAction.objects.create(
                            user=user,
                            action=action,
                            display_name=display_name,
                            icon=icon,
                            color=color,
                            order=order,
                            is_active=random.choice([True, True, True, False])
                        )
                        actions_created += 1
                    except Exception as e:
                        self.stdout.write(f'Error creating quick action: {e}')
                
                self.stdout.write(f'  Created {actions_created} quick actions for {username}')
                
            except Exception as e:
                self.stdout.write(f'Error creating user: {e}')
        
        # Özet
        total_devices = Device.objects.count()
        total_logs = UserLog.objects.count()
        total_actions = QuickAction.objects.count()
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\nFake data generation completed successfully!\n'
                f'Users created: {users_created}\n'
                f'Total devices: {total_devices}\n'
                f'Total logs: {total_logs}\n'
                f'Total quick actions: {total_actions}'
            )
        )
