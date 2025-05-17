
-- 1. kullanicilar
CREATE TABLE kullanicilar (
    id SERIAL PRIMARY KEY,
    tc_no VARCHAR(11) UNIQUE NOT NULL,
    ad VARCHAR(50) NOT NULL,
    soyad VARCHAR(50) NOT NULL,
    sifre BYTEA NOT NULL,
    dogum_tarihi DATE NOT NULL,
    cinsiyet VARCHAR(10) CHECK (cinsiyet IN ('Erkek', 'Kadın', 'Diğer')),
    email VARCHAR(100) UNIQUE NOT NULL,
    rol VARCHAR(10) CHECK (rol IN ('doktor', 'hasta')) NOT NULL,
    profil_resmi BYTEA,
    aktif_mi BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 2. doktor_hasta
CREATE TABLE doktor_hasta (
    id SERIAL PRIMARY KEY,
    doktor_id INT NOT NULL REFERENCES kullanicilar(id),
    hasta_id INT NOT NULL REFERENCES kullanicilar(id),
    UNIQUE (doktor_id, hasta_id)
);

-- 3. belirtiler
CREATE TABLE belirtiler (
    id SERIAL PRIMARY KEY,
    ad VARCHAR(50) UNIQUE NOT NULL,
    aciklama TEXT
);

-- 4. hasta_belirtileri
CREATE TABLE hasta_belirtileri (
    id SERIAL PRIMARY KEY,
    hasta_id INT NOT NULL REFERENCES kullanicilar(id),
    belirti_id INT NOT NULL REFERENCES belirtiler(id),
    tarih DATE NOT NULL
);

-- 5. diyet_turleri
CREATE TABLE diyet_turleri (
    id SERIAL PRIMARY KEY,
    ad VARCHAR(50) UNIQUE NOT NULL,
    aciklama TEXT
);

-- 6. egzersiz_turleri
CREATE TABLE egzersiz_turleri (
    id SERIAL PRIMARY KEY,
    ad VARCHAR(50) UNIQUE NOT NULL,
    aciklama TEXT
);

-- 7. diyet_takibi
CREATE TABLE diyet_takibi (
    id SERIAL PRIMARY KEY,
    hasta_id INT NOT NULL REFERENCES kullanicilar(id),
    tarih DATE NOT NULL,
    durum BOOLEAN NOT NULL,
    diyet_turu_id INT NOT NULL REFERENCES diyet_turleri(id)
);

-- 8. egzersiz_takibi
CREATE TABLE egzersiz_takibi (
    id SERIAL PRIMARY KEY,
    hasta_id INT NOT NULL REFERENCES kullanicilar(id),
    tarih DATE NOT NULL,
    durum BOOLEAN NOT NULL,
    egzersiz_turu_id INT NOT NULL REFERENCES egzersiz_turleri(id)
);

-- 9. olcum_zamanlari
CREATE TABLE olcum_zamanlari (
    id SERIAL PRIMARY KEY,
    ad VARCHAR(20) UNIQUE NOT NULL,
    saat_baslangic TIME NOT NULL,
    saat_bitis TIME NOT NULL
);

-- 10. kan_sekeri_olcumleri
CREATE TABLE kan_sekeri_olcumleri (
    id SERIAL PRIMARY KEY,
    hasta_id INT NOT NULL REFERENCES kullanicilar(id),
    olcum_zamani TIMESTAMPTZ NOT NULL,
    olcum_zamani_id INT REFERENCES olcum_zamanlari(id),
    seviye INT NOT NULL CHECK (seviye >= 0)
);

-- 11. uyarilar
CREATE TABLE uyarilar (
    id SERIAL PRIMARY KEY,
    hasta_id INT NOT NULL REFERENCES kullanicilar(id),
    tarih DATE NOT NULL,
    uyarı_tipi VARCHAR(30) NOT NULL,
    mesaj TEXT NOT NULL,
    bildirildi BOOLEAN DEFAULT FALSE
);

-- 12. loglar
CREATE TABLE loglar (
    id SERIAL PRIMARY KEY,
    kullanici_id INT REFERENCES kullanicilar(id),
    islem TEXT NOT NULL,
    zaman TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 13. hasta_notlari
CREATE TABLE hasta_notlari (
    id SERIAL PRIMARY KEY,
    doktor_id INT REFERENCES kullanicilar(id),
    hasta_id INT REFERENCES kullanicilar(id),
    tarih TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    not_metni TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS olcum_zamanlari (
    id SERIAL PRIMARY KEY,
    ad VARCHAR(20) UNIQUE NOT NULL,
    saat_baslangic TIME NOT NULL,
    saat_bitis TIME NOT NULL
);

-- 14. insulin_onerileri
CREATE TABLE insulin_onerileri (
    id SERIAL PRIMARY KEY,
    hasta_id INT NOT NULL REFERENCES kullanicilar(id) ON DELETE CASCADE,
    tarih DATE NOT NULL,
    ortalama NUMERIC(5,2) NOT NULL,
    doz_ml INT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (hasta_id, tarih)
);

-- Saat aralıklarını ekleyelim
INSERT INTO olcum_zamanlari (ad, saat_baslangic, saat_bitis) VALUES
('Sabah', '07:00', '08:00'),
('Öğle', '12:00', '13:00'),
('İkindi', '15:00', '16:00'),
('Akşam', '18:00', '19:00'),
('Gece', '22:00', '23:00');


ALTER TABLE uyarilar
RENAME COLUMN "uyari_tipi" TO uyari_tipi;
-- Gerekli uzantıyı yükle (zaten yüklü ama güvence için burada da belirtiyoruz)
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Sabit Doktor Kaydı (TC: 99999999999, Şifre: admin123)
INSERT INTO kullanicilar (tc_no, ad, soyad, sifre, dogum_tarihi, cinsiyet, email, rol)
VALUES
('99999999999', 'Admin', 'Doktor', decode(encode(digest('admin123', 'sha256'), 'hex'), 'hex'), '1980-01-01', 'Erkek', 'admin@example.com', 'doktor')
ON CONFLICT (tc_no) DO NOTHING;

SELECT tc_no, ad, sifre FROM kullanicilar WHERE tc_no = '99999999999';

DELETE FROM uyarilar a
USING uyarilar b
WHERE a.ctid < b.ctid
  AND a.hasta_id = b.hasta_id
  AND a.tarih = b.tarih
  AND a.uyari_tipi = b.uyari_tipi
  AND a.mesaj = b.mesaj;


ALTER TABLE uyarilar
ADD CONSTRAINT uyarilar_unique
UNIQUE (hasta_id, tarih, uyari_tipi, mesaj);

ALTER TABLE uyarilar ADD COLUMN gosterildi BOOLEAN DEFAULT FALSE;

INSERT INTO kullanicilar (
    tc_no, ad, soyad, sifre, dogum_tarihi, cinsiyet, email, rol
) VALUES (
    '77777777777',
    'Ali',
    'Veli',
    decode(encode(digest('456', 'sha256'), 'hex'), 'hex'),
    '1990-01-01',
    'Erkek',
    'ali.veli@example.com',
    'hasta'
);

INSERT INTO kullanicilar (
    tc_no, ad, soyad, sifre, dogum_tarihi, cinsiyet, email, rol
) VALUES (
    '666666666666',
    'Mehmet',
    'Işık',
    decode(encode(digest('456', 'sha256'), 'hex'), 'hex'),
    '1995-05-01',
    'Erkek',
    'mehmet_isik@example.com',
    'hasta'
);



INSERT INTO kullanicilar
(tc_no, ad, soyad, sifre, dogum_tarihi, cinsiyet, email, rol)
VALUES
('88888888888', 'Ayşe', 'Demir', digest('234', 'sha256'), '1995-06-12', 'Kadın', 'ayse@example.com', 'hasta');

INSERT INTO kullanicilar
(tc_no, ad, soyad, sifre, dogum_tarihi, cinsiyet, email, rol)
VALUES
('66666666666', 'Furkan', 'Yıldız', digest('135', 'sha256'), '2000-04-17', 'Erkek', 'furkanyildiz@example.com', 'hasta');


INSERT INTO kullanicilar (tc_no, ad, soyad, sifre, dogum_tarihi, cinsiyet, email, rol)
VALUES (
    '99999999991',                     -- TC
    'Ahmet',                           -- Ad
    'Yılmaz',                          -- Soyad
    digest('d234', 'sha256'),     -- Şifre (şifreli)
    '1980-05-10',                      -- Doğum Tarihi
    'Erkek',                           -- Cinsiyet
    'ahmet.yilmaz@example.com',       -- E-posta
    'doktor'                          -- Rol
);

INSERT INTO kullanicilar
(tc_no, ad, soyad, sifre, dogum_tarihi, cinsiyet, email, rol)
VALUES
('88888888881', 'Yavuz', 'Bilgin', digest('178', 'sha256'), '2001-02-04', 'Erkek', 'yavuz@example.com', 'hasta');



DROP TABLE IF EXISTS public.diyet_takibi CASCADE;

DROP TABLE IF EXISTS public.egzersiz_takibi CASCADE;

-- Diyet takibi tablosuna
ALTER TABLE diyet_takibi
ADD COLUMN hasta_ad TEXT,
ADD COLUMN hasta_tc VARCHAR(11);

-- Egzersiz takibi tablosuna
ALTER TABLE egzersiz_takibi
ADD COLUMN hasta_ad TEXT,
ADD COLUMN hasta_tc VARCHAR(11);

CREATE TABLE diyet_takibi (
    id SERIAL PRIMARY KEY,
    hasta_id INTEGER REFERENCES kullanicilar(id),
    tarih DATE NOT NULL,
    saat TIME NOT NULL,
    durum BOOLEAN DEFAULT TRUE,
    diyet_turu_id INTEGER REFERENCES diyet_turleri(id),
    hasta_ad TEXT,
    hasta_tc VARCHAR(11)
);

CREATE TABLE egzersiz_takibi (
    id SERIAL PRIMARY KEY,
    hasta_id INTEGER REFERENCES kullanicilar(id),
    tarih DATE NOT NULL,
    saat TIME NOT NULL,
    durum BOOLEAN DEFAULT TRUE,
    egzersiz_turu_id INTEGER REFERENCES egzersiz_turleri(id),
    hasta_ad TEXT,
    hasta_tc VARCHAR(11)
);
