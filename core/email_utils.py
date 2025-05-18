import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_login_email(email: str, password: str, tc_no: str) -> None:
    # GÖNDEREN BİLGİLERİ — Gmail üzerinden test ediyorsan aşağıyı düzenle
    GONDEREN_EMAIL = "elifceler55@gmail.com"
    GONDEREN_SIFRE = "dgix xpia tfth qzza"  # Gmail için özel uygulama şifresi alman gerekir
    SMTP_SERVER = "smtp.gmail.com"
    SMTP_PORT = 587

    # Mail içeriği
    konu = "Diyabet Takip Sistemi Giriş Bilgileri"
    mesaj = f"""Merhaba,

Diyabet Takip Sistemine giriş yapmak için aşağıdaki bilgileri kullanabilirsiniz:

👤 Kullanıcı Adı (TC): {tc_no}
📧 E-posta: {email}
🔑 Şifre : {password}

Sağlıklı günler dileriz.
"""

    msg = MIMEMultipart()
    msg["From"] = GONDEREN_EMAIL
    msg["To"] = email
    msg["Subject"] = konu
    msg.attach(MIMEText(mesaj, "plain"))

    # Mail gönderimi
    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(GONDEREN_EMAIL, GONDEREN_SIFRE)
        server.send_message(msg)
        server.quit()
    except Exception as e:
        raise RuntimeError(f"E-posta gönderimi başarısız oldu: {e}")
