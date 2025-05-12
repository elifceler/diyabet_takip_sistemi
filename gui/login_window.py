import tkinter as tk
from tkinter import messagebox
from core.database import Database
from gui.doctor_window import run_doctor
from gui.patient_window import run_patient

def run_login(expected_role: str):
    db = Database()                     # tek DB nesnesi; her giriş denemesinde bağlan-kapat

    def try_login():
        tc = entry_tc.get().strip()
        pw = entry_pw.get().strip()

        db.connect()
        info = db.login_user(tc, pw)    # yeni login_user sözlük döndürüyor
        db.close()

        if not info:
            messagebox.showerror("Hata", "TC veya şifre yanlış!")
            return

        if info["rol"] != expected_role:
            messagebox.showerror("Hata",
                                 f"Bu ekran yalnızca {expected_role} girişi içindir!")
            return

        # başarı → login penceresini kapat ve ilgili pencereye geç
        root.destroy()
        if info["rol"] == "doktor":
            run_doctor(info)            # info sözlüğünü ilet
        else:
            run_patient(info)

    # ---------- UI ----------
    root = tk.Tk()
    root.title(f"{expected_role.capitalize()} Girişi")
    root.geometry("300x180")

    tk.Label(root, text=f"{expected_role.capitalize()} Girişi",
             font=("Arial", 14)).pack(pady=10)

    tk.Label(root, text="TC Kimlik No:").pack()
    entry_tc = tk.Entry(root)
    entry_tc.pack()

    tk.Label(root, text="Şifre:").pack(pady=5)
    entry_pw = tk.Entry(root, show="*")
    entry_pw.pack()

    tk.Button(root, text="Giriş Yap", command=try_login).pack(pady=12)

    root.mainloop()
