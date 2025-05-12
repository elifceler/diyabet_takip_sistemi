from core.database import Database

def add_patient(doktor_id, tc_no, ad, soyad,
                password, email, dogum_tarihi, cinsiyet):
    db = Database(); db.connect()

    db.add_user(tc_no, ad, soyad, password,
                dogum_tarihi, cinsiyet, email, "hasta")

    # dokter_id artık doğrudan id (int)
    db.execute_query("""
        INSERT INTO doktor_hasta (doktor_id, hasta_id)
        VALUES (%s,
                (SELECT id FROM kullanicilar WHERE tc_no = %s))
        ON CONFLICT DO NOTHING;
    """, (doktor_id, tc_no))

    db.close()


def send_email(email, subject, content):
    """
    Kullanıcıya e-posta gönderme
    """
    print(f"E-posta gönderildi: {email}")
    print(f"Konu: {subject}")
    print(f"İçerik: {content}")

def delete_patient(hasta_id):
    """
    Verilen hasta_id'ye sahip hastayı siler.
    - Hem kullanicilar tablosundan hem de doktor_hasta ilişkisinden kaldırır.
    """
    db = Database()
    db.connect()

    try:
        # 1. doktor_hasta ilişkisinden sil
        db.execute_query("""
            DELETE FROM doktor_hasta WHERE hasta_id = %s;
        """, (hasta_id,))

        # 2. kullanicilar tablosundan sil
        db.execute_query("""
            DELETE FROM kullanicilar WHERE id = %s;
        """, (hasta_id,))

        print(f"Hasta ID {hasta_id} veritabanından silindi.")
    except Exception as e:
        print(f"Hasta silme hatası: {e}")
        raise e
    finally:
        db.close()

