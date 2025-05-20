import tkinter as tk
from PIL import Image, ImageTk
import os
from core.database import Database
from gui.profil_window import upload_profile_picture

def open_kisi_bilgisi_window(user_id: int):
    win = tk.Toplevel()
    win.title("Kişi Bilgileri")
    win.geometry("350x450")
    win.resizable(False, False)

    db = Database(); db.connect()
    row = db.fetch_one("""
        SELECT ad, soyad, tc_no, dogum_tarihi, email, profil_resmi_path
        FROM kullanicilar WHERE id = %s;
    """, (user_id,))
    db.close()

    if not row:
        tk.Label(win, text="Kullanıcı bilgisi bulunamadı!", fg="red").pack(pady=20)
        return

    ad, soyad, tc, dogum, email, img_path = row

    # Profil fotoğrafı
    img_label = tk.Label(win)
    img_label.pack(pady=10)

    if img_path and os.path.exists(img_path):
        img = Image.open(img_path)
        img = img.resize((120, 120))
        photo = ImageTk.PhotoImage(img)
        img_label.config(image=photo)
        img_label.image = photo

    # Kullanıcı bilgileri
    info_frame = tk.Frame(win)
    info_frame.pack(pady=10)

    entries = [
        ("Ad Soyad", f"{ad} {soyad}"),
        ("TC Kimlik No", tc),
        ("Doğum Tarihi", dogum.strftime("%d.%m.%Y")),
        ("E-posta", email),
    ]

    for label_text, value in entries:
        tk.Label(info_frame, text=label_text + ":", font=("Arial", 10, "bold")).pack(anchor="w")
        tk.Label(info_frame, text=value).pack(anchor="w", pady=(0, 6))

    # 🔵 Buton doğru yerde, sadece bir kez
    tk.Button(
        win,
        text="Profil Fotoğrafı Yükle",
        command=lambda: upload_profile_picture(user_id, img_label),
        bg="#2196F3", fg="white"
    ).pack(pady=10)
