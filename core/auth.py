from core.database import Database
from hashlib import sha256

def hash_password(password: str) -> bytes:
    """ Şifreyi SHA-256 ile hashler """
    return sha256(password.encode()).digest()

def login(tc_no: str, plain_pw: str):
    """
    Kullanıcı girişi yapar ve kullanıcı bilgilerini döner.
    Dönüş formatı: {'id': int, 'ad': str, 'soyad': str, 'rol': str}
    """
    db = Database()
    db.connect()
    user = db.get_user_by_tc(tc_no)
    db.close()

    if not user:
        print("Kullanıcı bulunamadı!")
        return None

    # Şifre kontrolü
    stored_password = user[4]
    hashed_input_password = hash_password(plain_pw)

    if stored_password == hashed_input_password:
        # Kullanıcı bilgilerini döndür
        return {
            "id": user[0],
            "ad": user[2],
            "soyad": user[3],
            "rol": user[8]
        }

    print("Şifre hatalı!")
    return None
