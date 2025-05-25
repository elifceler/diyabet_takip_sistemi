import psycopg2
from data.config import DATABASE_CONFIG
import hashlib
from datetime import datetime

class Database:
    def __init__(self):
        self.connection = None

    def connect(self):
        """ Veritabanı bağlantısını kurar """
        try:
            self.connection = psycopg2.connect(
                dbname=DATABASE_CONFIG['dbname'],
                user=DATABASE_CONFIG['user'],
                password=DATABASE_CONFIG['password'],
                host=DATABASE_CONFIG['host'],
                port=DATABASE_CONFIG['port']
            )
            print("Veritabanına bağlanıldı.")
        except Exception as e:
            print(f"Veritabanı bağlantı hatası: {e}")

    def close(self):
        """ Veritabanı bağlantısını kapatır """
        if self.connection:
            self.connection.close()
            print("Veritabanı bağlantısı kapatıldı.")

    def execute_query(self, query, params=None):
        """ Sorgu çalıştırır ve hata kontrolü yapar """
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query, params or ())
                self.connection.commit()
                print("Sorgu başarıyla çalıştırıldı.")
        except Exception as e:
            print(f"Sorgu çalıştırma hatası: {e}")
            self.connection.rollback()

    def fetch_one(self, query, params=None):
        """ Tek bir kayıt döner """
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query, params or ())
                result = cursor.fetchone()

                # Eğer kayıt bulunamadıysa `None` döner
                if not result:
                    return None

                # Result bir tuple ise list'e dönüştür
                result = list(result)

                # Eğer şifre alanı `memoryview` tipindeyse, bytes'e dönüştür
                if len(result) > 4 and isinstance(result[4], memoryview):
                    result[4] = bytes(result[4])

                return tuple(result)

        except Exception as e:
            print(f"Veri çekme hatası: {e}")
            return None

    def fetch_all(self, query, params=None):
        """ Tüm kayıtları döner """
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query, params or ())
                return cursor.fetchall()
        except Exception as e:
            print(f"Veri çekme hatası: {e}")
            return []

    def add_user(self, tc_no, ad, soyad, sifre, dogum_tarihi,
                 cinsiyet, email, rol):

        if self.get_user_by_tc(tc_no):
            print(f"Bu TC numarası zaten mevcut: {tc_no}")
            return

        hashed_password = self.hash_password(sifre)  # fonksiyon str/bytes ayırıyor

        query = """
            INSERT INTO public.kullanicilar
            (tc_no, ad, soyad, sifre, dogum_tarihi, cinsiyet, email, rol)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
        """
        params = (tc_no, ad, soyad, hashed_password,
                  dogum_tarihi, cinsiyet, email, rol)
        self.execute_query(query, params)

    def get_user_by_tc(self, tc_no):
        """ TC numarasına göre kullanıcı getir """
        query = "SELECT * FROM public.kullanicilar WHERE tc_no = %s;"
        params = (tc_no,)
        return self.fetch_one(query, params)

    def hash_password(self, password):
        """
        Tek noktada hash’leme:
        - Eğer zaten bytes ise dokunma
        - Değilse (str) SHA‑256 uygula
        """
        if isinstance(password, bytes):
            return password  # zaten hash’lenmiş
        return hashlib.sha256(password.encode()).digest()

    def login_user(self, tc_no: str, password: str):
        """
        • TC kimliği + parola alır
        • Parolayı hash'leyip veritabanındaki BYTEA ile karşılaştırır
        • Başarılıysa kullanıcı bilgilerini sözlük olarak döndürür
          { id, ad, soyad, email, rol }
        • Başarısızsa None döndürür
        """
        # 1. Kullanıcıyı TC'ye göre çek
        user = self.fetch_one(
            "SELECT * FROM public.kullanicilar WHERE tc_no = %s;",
            (tc_no,)
        )

        if not user:  # TC bulunamadı
            print("Kullanıcı bulunamadı!")
            return None

        stored_password = user[4]  # BYTEA saklı şifre
        # 2. Girilen parolayı tek noktada hash'le
        if stored_password == self.hash_password(password):
            print("Giriş başarılı!")
            role = user[8]  # 8. sütun → rol (“doktor” / “hasta”)
            return {
                "id": user[0],
                "ad": user[2],
                "soyad": user[3],
                "email": user[6],
                "rol": role
            }

        # Şifre uyuşmadı
        print("Şifre hatalı!")
        return None

    def add_alert(self, hasta_id, tarih, uyari_tipi, mesaj):
        """ Uyarı ekleme """
        query = """
            INSERT INTO public.uyarilar (hasta_id, tarih, uyari_tipi, mesaj, bildirildi)
            VALUES (%s, %s, %s, %s, FALSE);
        """
        params = (hasta_id, tarih, uyari_tipi, mesaj)
        self.execute_query(query, params)
        print(f"Uyarı eklendi: {uyari_tipi} - {mesaj}")


    def check_blood_sugar_alert(self, hasta_id, seviye):
        """ Kan şekeri seviyesine göre uyarı oluşturur """
        now = datetime.now()

        # Düşük kan şekeri uyarısı
        if seviye < 70:
            mesaj = f"Kan şekeri seviyesi çok düşük: {seviye} mg/dL"
            self.add_alert(hasta_id, now, "Düşük Kan Şekeri", mesaj)

        # Yüksek kan şekeri uyarısı
        elif seviye > 180:
            mesaj = f"Kan şekeri seviyesi çok yüksek: {seviye} mg/dL"
            self.add_alert(hasta_id, now, "Yüksek Kan Şekeri", mesaj)

    def add_blood_sugar_log(self, hasta_id, olcum_zamani, olcum_zamani_id, seviye):
        """ Kan şekeri ölçümü ekleme """
        query = """
            INSERT INTO public.kan_sekeri_olcumleri (hasta_id, olcum_zamani, olcum_zamani_id, seviye)
            VALUES (%s, %s, %s, %s);
        """
        params = (hasta_id, olcum_zamani, olcum_zamani_id, seviye)
        self.execute_query(query, params)
        print(f"Kan şekeri kaydı eklendi: Hasta ID = {hasta_id}, Zaman = {olcum_zamani}, Seviye = {seviye}")

        # Uyarı kontrolü
        self.check_blood_sugar_alert(hasta_id, seviye)
        self._update_daily_insulin(hasta_id, olcum_zamani.date())
        self.check_insulin_data_alert(hasta_id, olcum_zamani.date())

    def get_insulin_suggestions(self, hasta_id):
        return self.fetch_all("""
            SELECT tarih, ortalama, doz_ml
            FROM insulin_onerileri
            WHERE hasta_id = %s
            ORDER BY tarih DESC;
        """, (hasta_id,))

    def get_alerts(self, hasta_id):
        """Hastaya ait bildirilmeyen uyarıları getir ve gösterildikten sonra işaretle."""
        query = """
            SELECT id, tarih, uyari_tipi, mesaj, bildirildi
            FROM public.uyarilar
            WHERE hasta_id = %s AND bildirildi = FALSE
            ORDER BY tarih DESC;
        """
        params = (hasta_id,)
        alerts = self.fetch_all(query, params)

        # Bildirildi olarak işaretle (bir daha gösterilmemesi için)
        for alert in alerts:
            alert_id = alert[0]
            self.execute_query("""
                UPDATE public.uyarilar
                SET bildirildi = TRUE
                WHERE id = %s;
            """, (alert_id,))

        # Tarih formatını dönüştür
        formatted_alerts = []
        for alert in alerts:
            alert_id, tarih, uyari_tipi, mesaj, bildirildi = alert
            formatted_tarih = tarih.strftime("%d.%m.%Y")
            formatted_alerts.append((alert_id, formatted_tarih, uyari_tipi, mesaj, bildirildi))

        return formatted_alerts



    def _dose_for_avg(self, avg):
        dose_rules = [
            (70, 0), (110, 0), (150, 1), (200, 2), (9999, 3)
        ]
        for limit, dose in dose_rules:
            if avg <= limit:
                return dose

    def _update_daily_insulin(self, hasta_id: int, the_date):
        rows = self.fetch_all("""
            SELECT seviye FROM kan_sekeri_olcumleri
            WHERE hasta_id = %s AND DATE(olcum_zamani) = %s AND olcum_zamani_id IS NOT NULL;
        """, (hasta_id, the_date))

        if not rows:
            return

        seviyeler = [r[0] for r in rows]
        if len(seviyeler) < 3:
            ort = sum(seviyeler) / len(seviyeler)
            doz = self._dose_for_avg(ort)  # Öneriyi yine de ver
        else:
            ort = sum(seviyeler) / len(seviyeler)
            doz = self._dose_for_avg(ort)

        self.execute_query("""
            INSERT INTO insulin_onerileri (hasta_id, tarih, ortalama, doz_ml)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (hasta_id, tarih) DO UPDATE
            SET ortalama = EXCLUDED.ortalama,
                doz_ml = EXCLUDED.doz_ml,
                created_at = CURRENT_TIMESTAMP;
        """, (hasta_id, the_date, ort, doz))

    def check_insulin_data_alert(self, hasta_id: int, the_date):
        """
        Belirli bir tarihteki ölçümleri kontrol eder ve eksik/yetersizse uyarı ekler.
        """
        # Aynı güne ait önceki insulin uyarılarını sil
        self.execute_query("""
            DELETE FROM uyarilar
            WHERE hasta_id = %s AND DATE(tarih) = %s AND uyari_tipi IN ('Eksik Ölçüm', 'Yetersiz Ölçüm');
        """, (hasta_id, the_date))

        rows = self.fetch_all("""
            SELECT seviye, olcum_zamani_id
            FROM kan_sekeri_olcumleri
            WHERE hasta_id = %s AND DATE(olcum_zamani) = %s;
        """, (hasta_id, the_date))

        seviyeler = [r[0] for r in rows if r[1] is not None]
        eksik_miktar = 5 - len(seviyeler)

        if len(seviyeler) < 3:
            # Yetersiz veri
            mesaj1 = f"{the_date.strftime('%d.%m.%Y')} tarihli ölçümler yetersiz! Ortalama güvenilir değil."
            self._add_insulin_alert_once(hasta_id, the_date, "Yetersiz Ölçüm", mesaj1)

            # Aynı zamanda eksik ölçüm uyarısı da verilmeli
            eksik_miktar = 5 - len(seviyeler)
            mesaj2 = f"{the_date.strftime('%d.%m.%Y')} tarihinde {eksik_miktar} ölçüm eksik. Ortalama eksik verilere göre hesaplandı."
            self._add_insulin_alert_once(hasta_id, the_date, "Eksik Ölçüm", mesaj2)


        elif eksik_miktar > 0:
            mesaj = "Ölçüm eksik! Ortalama alınırken bu ölçüm hesaba katılmadı."
            self._add_insulin_alert_once(hasta_id, the_date, "Eksik Ölçüm", mesaj)

    def _add_insulin_alert_once(self, hasta_id, tarih, tip, mesaj):
        """
        Aynı tarih ve aynı mesaj için tekrar tekrar uyarı eklemeyi önler.
        """
        var_mi = self.fetch_one("""
            SELECT id FROM uyarilar
            WHERE hasta_id = %s AND tarih = %s AND uyari_tipi = %s AND mesaj = %s;
        """, (hasta_id, tarih, tip, mesaj))

        if not var_mi:
            self.add_alert(hasta_id, tarih, tip, mesaj)

    def check_daily_blood_sugar_alerts_for_doctor(self, hasta_id: int, date_obj):
        """Her ölçüm sonrası çalışır, o güne dair tüm verileri analiz edip uyarı ekler"""
        rows = self.fetch_all("""
            SELECT seviye, olcum_zamani
            FROM kan_sekeri_olcumleri
            WHERE hasta_id = %s AND DATE(olcum_zamani) = %s
        """, (hasta_id, date_obj))

        seviyeler = [r[0] for r in rows]

        # 1. Hiç ölçüm yoksa
        if not seviyeler:
            self.add_alert(
                hasta_id, date_obj,
                "Ölçüm Eksik Uyarısı",
                "Hasta gün boyunca kan şekeri ölçümü yapmamıştır. Acil takip önerilir."
            )
            return

        # 2. Ölçüm sayısı < 3
        if len(seviyeler) < 3:
            self.add_alert(
                hasta_id, date_obj,
                "Ölçüm Yetersiz Uyarısı",
                "Hastanın günlük kan şekeri ölçüm sayısı yetersiz (<3). Durum izlenmelidir."
            )

        # 3. Ölçüm seviyelerine göre detaylı doktor uyarıları
        for seviye in seviyeler:
            if seviye < 70:
                self.add_alert(
                    hasta_id, date_obj,
                    "Acil Uyarı",
                    "Hastanın kan şekeri seviyesi 70 mg/dL'nin altına düştü. Hipoglisemi riski! Hızlı müdahale gerekebilir."
                )
            elif 111 <= seviye <= 150:
                self.add_alert(
                    hasta_id, date_obj,
                    "Takip Uyarısı",
                    "Hastanın kan şekeri 111-150 mg/dL arasında. Durum izlenmeli."
                )
            elif 151 <= seviye <= 200:
                self.add_alert(
                    hasta_id, date_obj,
                    "İzleme Uyarısı",
                    "Hastanın kan şekeri 151-200 mg/dL arasında. Diyabet kontrolü gereklidir."
                )
            elif seviye > 200:
                self.add_alert(
                    hasta_id, date_obj,
                    "Acil Müdahale Uyarısı",
                    "Hastanın kan şekeri 200 mg/dL'nin üzerinde. Hiperglisemi durumu. Acil müdahale gerekebilir."
                )

    def check_first_time_measurement_alert(self, hasta_id: int):
        """Hasta daha önce hiç ölçüm yapmadıysa genel bir uyarı oluşturur."""
        count = self.fetch_one("""
            SELECT COUNT(*) FROM kan_sekeri_olcumleri
            WHERE hasta_id = %s
        """, (hasta_id,))

        if count and count[0] == 0:
            mesaj = "Hasta henüz hiç kan şekeri ölçümü yapmamıştır. Takip önerilir."
            self.add_alert(hasta_id, datetime.today().date(), "İlk Ölçüm Eksik", mesaj)

    def get_doctor_alerts(self, hasta_id):
        """
        Doktora gösterilecek TÜM uyarıları döndürür.
        Sadece doktor tipi uyarılar: 'Acil Uyarı', 'Takip Uyarısı', 'İzleme Uyarısı',
        'Acil Müdahale Uyarısı', 'Ölçüm Eksik Uyarısı', 'Ölçüm Yetersiz Uyarısı'
        """
        query = """
            SELECT id, tarih, uyari_tipi, mesaj, bildirildi
            FROM public.uyarilar
            WHERE hasta_id = %s
            AND uyari_tipi IN (
                'Acil Uyarı',
                'Takip Uyarısı',
                'İzleme Uyarısı',
                'Acil Müdahale Uyarısı',
                'Ölçüm Eksik Uyarısı',
                'Ölçüm Yetersiz Uyarısı'
            )
            ORDER BY tarih DESC;
        """
        return self.fetch_all(query, (hasta_id,))

    def generate_all_doctor_alerts(self, hasta_id: int):
        # Hastanın ölçüm yaptığı bütün tarihleri çek
        dates = self.fetch_all("""
            SELECT DISTINCT DATE(olcum_zamani)
            FROM kan_sekeri_olcumleri
            WHERE hasta_id = %s;
        """, (hasta_id,))

        for (d,) in dates:
            self.check_daily_blood_sugar_alerts_for_doctor(hasta_id, d)

    def get_recommendation_progress(self, hasta_id: int):
        """Hastanın uyguladığı diyet ve egzersizlerin oranını döner: (diyet_oran, egzersiz_oran)"""
        # Diyet
        total_diyet = self.fetch_one(
            "SELECT COUNT(*) FROM diyet_takibi WHERE hasta_id = %s;", (hasta_id,)
        )[0]
        applied_diyet = self.fetch_one(
            "SELECT COUNT(*) FROM diyet_takibi WHERE hasta_id = %s AND durum = TRUE;", (hasta_id,)
        )[0]

        # Egzersiz
        total_egz = self.fetch_one(
            "SELECT COUNT(*) FROM egzersiz_takibi WHERE hasta_id = %s;", (hasta_id,)
        )[0]
        applied_egz = self.fetch_one(
            "SELECT COUNT(*) FROM egzersiz_takibi WHERE hasta_id = %s AND durum = TRUE;", (hasta_id,)
        )[0]

        # Yüzde hesapla
        diyet_oran = round((applied_diyet / total_diyet) * 100, 1) if total_diyet > 0 else 0
        egz_oran = round((applied_egz / total_egz) * 100, 1) if total_egz > 0 else 0

        return diyet_oran, egz_oran

    def get_insulin_averages_for_graph(self, hasta_id):
        """
        Hazır günlük ortalama kan şekeri seviyelerini insulin_onerileri tablosundan getirir.
        """
        return self.fetch_all("""
            SELECT tarih, ortalama
            FROM insulin_onerileri
            WHERE hasta_id = %s
            ORDER BY tarih;
        """, (hasta_id,))

    def get_diet_exercise_blood_sugar_graph_data(self, hasta_id: int):
        return self.fetch_all("""
            SELECT dt.tarih,
                   dtr.ad AS diyet_adi,
                   dt.durum AS diyet_uygulandi,
                   et.durum AS egzersiz_uygulandi,
                   io.ortalama
            FROM diyet_takibi dt
            JOIN diyet_turleri dtr ON dt.diyet_turu_id = dtr.id
            LEFT JOIN egzersiz_takibi et
                ON dt.hasta_id = et.hasta_id AND dt.tarih = et.tarih
            LEFT JOIN insulin_onerileri io
                ON dt.hasta_id = io.hasta_id AND dt.tarih = io.tarih
            WHERE dt.hasta_id = %s
            ORDER BY dt.tarih;
        """, (hasta_id,))

