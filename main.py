# main.py
import tkinter as tk
from gui.login_window import run_login

def run_entry():
    root = tk.Tk()
    root.title("Diyabet Takip Sistemi – Rol Seçimi")
    root.geometry("300x200")

    tk.Label(root, text="Giriş yapmak için rol seçin", font=("Arial", 12)).pack(pady=20)

    tk.Button(root, text="Doktor Girişi", width=20,
              command=lambda: open_login(root, "doktor")).pack(pady=10)

    tk.Button(root, text="Hasta Girişi", width=20,
              command=lambda: open_login(root, "hasta")).pack(pady=10)

    root.mainloop()

def open_login(parent, role):
    parent.destroy()
    run_login(role)

if __name__ == "__main__":
    run_entry()
