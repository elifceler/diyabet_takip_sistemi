# 🩺 Diyabet Takip Sistemi

Bu proje, diyabet hastalarının günlük kan şekeri ölçümlerini, diyet ve egzersiz takibini yapmalarını ve doktorlarla etkili şekilde bilgi paylaşmalarını sağlamak amacıyla geliştirilmiş bir masaüstü uygulamasıdır.

## 🚀 Özellikler

- 🧪 **Kan şekeri ölçüm girişi**
- 🍽️ **Diyet ve egzersiz öneri motoru**  
  Belirtiler ve kan şekeri aralığına göre kişiye özel öneriler üretir.
- 📊 **Grafiksel kan şekeri takibi**  
  Günlük/haftalık bazda gelişim grafikleri sunar.
- 🛎️ **Doktor uyarı sistemi**  
  Kritik ölçümler tespit edildiğinde doktora bildirim üretir.
- 📁 **Geçmiş öneri kayıtları**  
  Kullanıcılar geçmiş önerilerini görüntüleyebilir.
- 🔐 **Kullanıcı girişi**: Hasta & Doktor rolleri

## 🏗️ Kullanılan Teknolojiler

- Python (Tkinter ile GUI)
- PostgreSQL (veritabanı)
- SQLite opsiyonu da mümkündür
- Matplotlib (grafik çizimi)

## 🔧 Kurulum

1. Reposu klonlayın:
   ```bash
   git clone https://github.com/kullanici/diyabet_takip_sistemi.git
   cd diyabet_takip_sistemi

Sanal ortam oluşturun ve bağımlılıkları yükleyin:

bash
Kopyala
Düzenle
python -m venv venv
venv\Scripts\activate   # (Linux/macOS için: source venv/bin/activate)
pip install -r requirements.txt
Veritabanını kurun:

schema.sql dosyasını çalıştırarak PostgreSQL üzerinde tabloları oluşturun.

Uygulamayı başlatın:

bash
Kopyala
Düzenle
python main.py
📁 Proje Yapısı
core/ → İş mantığı (veritabanı, öneri motoru, e-posta, grafikler)

gui/ → Arayüz pencereleri

schema.sql → Veritabanı tablo tanımları

main.py → Uygulamanın giriş noktası
