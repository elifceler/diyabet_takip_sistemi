import tkinter as tk

def run_patient(info: dict):
    root = tk.Tk()
    root.title("Hasta Paneli")
    root.geometry("400x250")

    tk.Label(root, text=f"Hoşgeldiniz {info['ad']} {info['soyad']}",
             font=("Arial", 14)).pack(pady=20)

    tk.Label(root, text="Bu alana kendi ölçümlerinizi ekleyeceksiniz.",
             font=("Arial", 11)).pack(pady=10)

    root.mainloop()
