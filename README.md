# 🚀 Cihaz Takip Sistemi - Siber Güvenlik Web Uygulaması

Modern Django tabanlı cihaz yönetim ve takip sistemi. Siber güvenlik teması ile tasarlanmış, kullanıcı dostu arayüz.

## ✨ Özellikler

### 🔐 Kullanıcı Yönetimi
- **Rol Tabanlı Yetkilendirme**: Superadmin, Admin, User rolleri
- **Güvenli Kimlik Doğrulama**: TC Kimlik + Şifre ile giriş
- **Profil Yönetimi**: Profil resmi yükleme, bilgi güncelleme
- **Hesap Güvenliği**: 5 başarısız giriş sonrası hesap kilitleme
- **Aktivite Logları**: Tüm kullanıcı işlemleri kayıt altında

### 📱 Cihaz Yönetimi
- **Cihaz Kayıt**: GSM numarası, e-posta, cihaz türü
- **Cihaz Türleri**: Telefon, Tablet, Bilgisayar, IoT, Araç Kamerası, Araç Takip Cihazı, IP Kamera
- **Cihaz Birliği**: Grup bazlı cihaz organizasyonu
- **Durum Takibi**: Aktif/Pasif cihaz durumu
- **Filtreleme**: Kullanıcı, tür, tarih bazlı arama

### 📊 Dashboard ve İstatistikler
- **Gerçek Zamanlı İstatistikler**: Toplam kullanıcı, cihaz sayıları
- **Grafik Görselleştirme**: Chart.js ile interaktif grafikler
- **Cihaz Dağılımı**: Tür bazlı yüzdelik dağılımlar
- **Son 7 Gün Kayıtları**: Zaman serisi grafikleri
- **Kullanıcı Bazlı İstatistikler**: Kişisel cihaz sayıları

### 🎨 Modern Arayüz
- **8 Farklı Tema**: Açık, koyu, siber, gün batımı, okyanus, orman, lavanta, mercan
- **TailwindCSS**: Modern ve responsive tasarım
- **Cyber Tema**: Siber güvenlik odaklı görsel tasarım
- **Animasyonlar**: CSS animasyonları ve geçiş efektleri
- **Mobil Uyumlu**: Tüm cihazlarda mükemmel görünüm

## 🛠️ Teknoloji Stack

### Backend
- **Django 4.2.23 LTS**: Web framework
- **PostgreSQL**: Veritabanı (SQLite fallback)
- **Django REST Framework**: API desteği
- **Crispy Forms**: Form renderleme

### Frontend
- **TailwindCSS**: CSS framework
- **Chart.js**: Grafik kütüphanesi
- **Font Awesome**: İkon kütüphanesi
- **JavaScript ES6+**: Modern JavaScript

### Güvenlik
- **Django Auth**: Kullanıcı kimlik doğrulama
- **CSRF Koruması**: Cross-site request forgery koruması
- **Session Yönetimi**: Güvenli oturum yönetimi
- **Input Validasyonu**: Form veri doğrulama

## 🚀 Kurulum

### Gereksinimler
- Python 3.8+
- PostgreSQL 12+ (opsiyonel)
- pip (Python paket yöneticisi)

### 1. Repository'yi Klonlayın
```bash
git clone https://github.com/resul067142/yenirr.git
cd yenirr
```

### 2. Virtual Environment Oluşturun
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# veya
venv\Scripts\activate     # Windows
```

### 3. Bağımlılıkları Yükleyin
```bash
pip install -r requirements.txt
```

### 4. Veritabanını Yapılandırın
```bash
# PostgreSQL için
createdb cihaz_takip_db

# veya SQLite için (varsayılan)
# settings.py'de DATABASES ayarını kontrol edin
```

### 5. Migrasyonları Çalıştırın
```bash
python manage.py makemigrations
python manage.py migrate
```

### 6. Superuser Oluşturun
```bash
python manage.py createsuperuser
```

### 7. Uygulamayı Başlatın
```bash
python manage.py runserver
```

Tarayıcınızda `http://localhost:8000` adresine gidin.

## 📁 Proje Yapısı

```
yenirr/
├── cihaz_takip/          # Ana proje ayarları
├── users/                 # Kullanıcı yönetimi
├── devices/               # Cihaz yönetimi
├── dashboard/             # Dashboard ve istatistikler
├── templates/             # HTML template'leri
├── static/                # CSS, JS, resim dosyaları
├── media/                 # Kullanıcı yüklenen dosyalar
├── requirements.txt       # Python bağımlılıkları
└── README.md             # Bu dosya
```

## 🔧 Konfigürasyon

### Veritabanı Ayarları
`cihaz_takip/settings.py` dosyasında:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'cihaz_takip_db',
        'USER': 'postgres',
        'PASSWORD': 'your_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

### Statik Dosya Ayarları
```python
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
```

## 📱 Kullanım

### Kullanıcı Rolleri
- **Superadmin**: Tüm yetkilere sahip, admin yönetimi
- **Admin**: Kullanıcı ve cihaz yönetimi
- **User**: Kendi cihazlarını yönetme

### Cihaz Ekleme
1. "Cihazlarım" menüsüne gidin
2. "Yeni Cihaz Ekle" butonuna tıklayın
3. Gerekli bilgileri doldurun
4. "Kaydet" butonuna tıklayın

### Tema Değiştirme
1. Top bar'da tema butonlarına tıklayın
2. 8 farklı tema arasından seçim yapın
3. Tema tercihiniz otomatik kaydedilir

## 🔒 Güvenlik Özellikleri

- **Hesap Kilitleme**: 5 başarısız giriş sonrası
- **Aktivite Logları**: Tüm işlemler kayıt altında
- **Rol Tabanlı Erişim**: Yetki kontrolü
- **Input Validasyonu**: Güvenli veri girişi
- **CSRF Koruması**: Cross-site request forgery koruması

## 📊 API Desteği

Django REST Framework ile API desteği mevcuttur:

```bash
# Cihaz listesi
GET /api/devices/

# Kullanıcı listesi
GET /api/users/

# Cihaz detayı
GET /api/devices/{id}/
```

## 🧪 Test

```bash
# Testleri çalıştırın
python manage.py test

# Coverage raporu
coverage run --source='.' manage.py test
coverage report
```

## 📈 Performans

- **Database Optimizasyonu**: Select related, prefetch related
- **Caching**: Django cache framework
- **Static Files**: CDN desteği
- **Image Optimization**: Pillow ile resim işleme

## 🤝 Katkıda Bulunma

1. Fork yapın
2. Feature branch oluşturun (`git checkout -b feature/amazing-feature`)
3. Değişikliklerinizi commit edin (`git commit -m 'Add amazing feature'`)
4. Branch'inizi push edin (`git push origin feature/amazing-feature`)
5. Pull Request oluşturun

## 📄 Lisans

Bu proje MIT lisansı altında lisanslanmıştır. Detaylar için `LICENSE` dosyasına bakın.

## 📞 İletişim

- **Proje Sahibi**: Resul Aktaş
- **GitHub**: [@resul067142](https://github.com/resul067142)
- **Repository**: [yenirr](https://github.com/resul067142/yenirr)

## 🙏 Teşekkürler

- Django Community
- TailwindCSS Team
- Chart.js Contributors
- Font Awesome Team

---

⭐ Bu projeyi beğendiyseniz yıldız vermeyi unutmayın!
