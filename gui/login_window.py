import tkinter as tk
from tkinter import messagebox
from core.database import Database
from gui.doctor_window import run_doctor
from gui.patient_window import run_patient

def run_login(expected_role: str):
    db = Database()

    def try_login():
        tc = entry_tc.get().strip()
        pw = entry_pw.get().strip()

        db.connect()
        info = db.login_user(tc, pw)
        db.close()

        if not info:
            messagebox.showerror("Hata", "TC veya şifre yanlış!")
            return

        if info["rol"] != expected_role:
            messagebox.showerror("Hata", f"Bu ekran yalnızca {expected_role} girişi içindir!")
            return

        root.destroy()
        if info["rol"] == "doktor":
            run_doctor(info)
        else:
            run_patient(info)

    # ---------- UI ----------
    root = tk.Tk()
    root.title(f"{expected_role.capitalize()} Girişi")
    root.geometry("360x260")
    root.configure(bg="#f0f0f0")

    tk.Label(root, text=f"{expected_role.capitalize()} Girişi",
             font=("Arial", 16, "bold"),
             fg="#2E7D32", bg="#f0f0f0").pack(pady=(20, 5))

    tk.Label(root, text="Lütfen aşağıdaki TC No ve şifre bilgilerini giriniz.",
             font=("Arial", 10), bg="#f0f0f0", fg="#555555").pack()

    frm = tk.Frame(root, bg="#f0f0f0")
    frm.pack(pady=12)

    # TC girişi
    tk.Label(frm, text="TC Kimlik No:", font=("Arial", 11), bg="#f0f0f0").grid(row=0, column=0, sticky="e", padx=6, pady=6)
    entry_tc = tk.Entry(frm, width=25)
    entry_tc.grid(row=0, column=1, padx=6, pady=6)

    # Şifre girişi
    tk.Label(frm, text="Şifre:", font=("Arial", 11), bg="#f0f0f0").grid(row=1, column=0, sticky="e", padx=6, pady=6)
    entry_pw = tk.Entry(frm, width=25, show="*")
    entry_pw.grid(row=1, column=1, padx=6, pady=6)

    # Giriş butonu
    tk.Button(root, text="Giriş Yap",
              font=("Arial", 11), width=20,
              bg="#4CAF50", fg="white", activebackground="#45a049",
              command=try_login).pack(pady=16)

    root.mainloop()
