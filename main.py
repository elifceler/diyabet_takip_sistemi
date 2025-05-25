import tkinter as tk
from gui.login_window import run_login

def run_entry():
    root = tk.Tk()
    root.title("Diyabet Takip Sistemi – Rol Seçimi")
    root.geometry("420x320")
    root.configure(bg="#f0f0f0")

    # Üst başlık
    tk.Label(
        root,
        text="DİYABET TAKİP SİSTEMİNE HOŞGELDİNİZ",
        font=("Arial", 16, "bold"),
        fg="#2E7D32",
        bg="#f0f0f0"
    ).pack(pady=(20, 10))

    # Alt açıklama
    tk.Label(
        root,
        text="Giriş yapmak için rol seçin",
        font=("Arial", 12),
        fg="#333",
        bg="#f0f0f0"
    ).pack(pady=(0, 20))

    BTN_STYLE = dict(
        width=20,
        height=2,
        font=("Arial", 12),
        bg="#4CAF50",
        fg="white",
        activebackground="#45a049",
        relief="raised",
        bd=2
    )

    tk.Button(
        root,
        text="Doktor Girişi",
        command=lambda: open_login(root, "doktor"),
        **BTN_STYLE
    ).pack(pady=8)

    tk.Button(
        root,
        text="Hasta Girişi",
        command=lambda: open_login(root, "hasta"),
        **BTN_STYLE
    ).pack(pady=8)

    root.mainloop()

def open_login(parent, role):
    parent.destroy()
    run_login(role)

if __name__ == "__main__":
    run_entry()
