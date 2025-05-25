import tkinter as tk
from PIL import Image, ImageTk
import os
from core.database import Database
from gui.profil_window import upload_profile_picture

def open_kisi_bilgisi_window(user_id: int):
    win = tk.Toplevel()
    win.title("Kişi Bilgileri")
    win.configure(bg="#F8F9FA")
    win.resizable(False, False)

    outer = tk.Frame(win, bg="#F8F9FA")
    outer.pack(expand=True)

    db = Database(); db.connect()
    row = db.fetch_one("""
        SELECT ad, soyad, tc_no, dogum_tarihi, email, profil_resmi_path
        FROM kullanicilar WHERE id = %s;
    """, (user_id,))
    db.close()

    if not row:
        tk.Label(outer, text="Kullanıcı bilgisi bulunamadı!", fg="red", bg="#F8F9FA", font=("Segoe UI", 10)).pack(pady=20)
        return

    ad, soyad, tc, dogum, email, img_path = row

    # Profil resmi
    img_label = tk.Label(outer, bg="#F8F9FA")
    img_label.pack(pady=(30, 10))

    if img_path and os.path.exists(img_path):
        img = Image.open(img_path)
        img = img.resize((140, 140))
        photo = ImageTk.PhotoImage(img)
        img_label.config(image=photo)
        img_label.image = photo
    else:
        img_label.config(text="Profil fotoğrafı yok", fg="gray", font=("Segoe UI", 9, "italic"))

    # Kart görünümünde bilgileri tut
    card = tk.Frame(outer, bg="white", bd=1, relief="solid")
    card.pack(padx=20, pady=10, ipadx=20, ipady=20)

    entries = [
        ("Ad Soyad", f"{ad} {soyad}"),
        ("TC Kimlik No", tc),
        ("Doğum Tarihi", dogum.strftime("%d.%m.%Y")),
        ("E-posta", email),
    ]

    for label_text, value in entries:
        tk.Label(card, text=label_text + ":", font=("Segoe UI", 10, "bold"), bg="white", anchor="w").pack(fill="x", padx=10, pady=(4, 0))
        tk.Label(card, text=value, font=("Segoe UI", 10), bg="white", anchor="w", wraplength=300).pack(fill="x", padx=10, pady=(0, 6))

    # Profil fotoğrafı yükle butonu
    tk.Button(
        outer,
        text="Profil Fotoğrafı Yükle",
        command=lambda: upload_profile_picture(user_id, img_label),
        bg="#2196F3", fg="white",
        font=("Segoe UI", 10, "bold"),
        activebackground="#1976D2",
        relief="flat",
        padx=12, pady=6
    ).pack(pady=20)

