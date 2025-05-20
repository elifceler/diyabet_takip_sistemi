# gui/profil_window.py
import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk
import os
import shutil

from core.database import Database

def upload_profile_picture(user_id: int, img_label: tk.Label):
    filepath = filedialog.askopenfilename(
        title="Profil Fotoğrafı Seç",
        filetypes=[("Resim Dosyaları", "*.png *.jpg *.jpeg *.gif")]
    )
    if not filepath:
        return

    file_ext = os.path.splitext(filepath)[1]
    target_dir = "images"
    os.makedirs(target_dir, exist_ok=True)
    filename = f"user_{user_id}{file_ext}"
    target_path = os.path.join(target_dir, filename)

    shutil.copy(filepath, target_path)

    db = Database()
    db.connect()
    db.execute_query(
        "UPDATE kullanicilar SET profil_resmi_path = %s WHERE id = %s;",
        (target_path, user_id)
    )
    db.close()

    load_profile_picture(target_path, img_label)

def load_profile_picture(img_path: str, label: tk.Label):
    full_path = os.path.join(os.getcwd(), img_path)
    if os.path.exists(full_path):
        img = Image.open(full_path)
        img = img.resize((120, 120))
        photo = ImageTk.PhotoImage(img)
        label.config(image=photo)
        label.image = photo


def open_profile_window(user_id: int):
    win = tk.Toplevel()
    win.title("Profil Bilgileri")
    win.geometry("300x300")

    img_label = tk.Label(win)
    img_label.pack(pady=10)

    # veritabanından mevcut fotoğrafı yükle
    db = Database(); db.connect()
    row = db.fetch_one("SELECT profil_resmi_path FROM kullanicilar WHERE id = %s;", (user_id,))
    db.close()

    if row and row[0]:
        load_profile_picture(row[0], img_label)

    tk.Button(
        win,
        text="Profil Fotoğrafı Yükle",
        command=lambda: upload_profile_picture(user_id, img_label),
        bg="#2196F3", fg="white"
    ).pack(pady=10)

    win.mainloop()
