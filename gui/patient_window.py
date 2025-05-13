# gui/patient_window.py
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, date
from core.database import Database
from core.blood_sugar_ui import show   # ölçüm‑liste & insülin penceresi

# ------------------------------------------------------------------
# 1) ÖLÇÜM EKLEME PENCERESİ
# ------------------------------------------------------------------
def add_blood_sugar_ui(hasta_id: int) -> None:
    win = tk.Toplevel()
    win.title("Kan Şekeri Ekle")
    win.geometry("320x360")

    tk.Label(win, text="Kan Şekeri Ekle", font=("Arial", 14)).pack(pady=10)

    # --- Giriş alanları -------------------------------------------------
    def add_row(lbl: str) -> tk.Entry:
        tk.Label(win, text=lbl).pack(pady=4)
        e = tk.Entry(win, width=22)
        e.pack()
        return e

    seviye_entry = add_row("Seviye (mg/dL)")
    tarih_entry  = add_row("Tarih (GG.AA.YYYY)")
    saat_entry   = add_row("Saat (HH:MM)")

    # -------------------------------------------------------------------
    def kaydet() -> None:
        # ---- ham veriler
        seviye_str = seviye_entry.get().strip()
        tarih_str  = tarih_entry.get().strip()
        saat_str   = saat_entry.get().strip()

        # ---- boş alan kontrolü
        if not (seviye_str and tarih_str and saat_str):
            messagebox.showwarning("Uyarı", "Lütfen tüm alanları doldurun!")
            return

        try:
            # ---- seviye kontrolü
            if not seviye_str.isdigit():
                raise ValueError("Seviye sadece sayılardan oluşmalıdır.")
            seviye = int(seviye_str)
            if not 0 <= seviye <= 500:
                raise ValueError("Seviye 0‑500 aralığında olmalıdır.")

            # ---- tarih & saat kontrolü
            try:
                ts_str = f"{tarih_str} {saat_str}"
                olcum_dt = datetime.strptime(ts_str, "%d.%m.%Y %H:%M")
            except ValueError:
                raise ValueError("Tarih/Saat biçimi GG.AA.YYYY ve HH:MM olmalıdır.")

            if olcum_dt.date() > date.today():
                raise ValueError("Gelecekteki bir tarih girilemez.")

            # ---- otomatik ÖLÇÜM_ZAMANI belirleme
            db = Database(); db.connect()
            zaman_kayitlari = db.fetch_all(
                "SELECT id, saat_baslangic, saat_bitis FROM olcum_zamanlari"
            )
            zaman_id   = None
            ortalama_dahil = True

            for z_id, bas_str, bit_str in zaman_kayitlari:
                bas = datetime.strptime(str(bas_str), "%H:%M:%S").time()
                bit = datetime.strptime(str(bit_str), "%H:%M:%S").time()
                if bas <= olcum_dt.time() <= bit:
                    zaman_id = z_id
                    break

            if zaman_id is None:
                # Saat aralığı dışı: kaydet → ortalamaya katılmasın
                ortalama_dahil = False
                # ‑1 gibi kurgusal zaman_id kullanabiliriz ya da NULL bırakabiliriz.
                # Ben NULL bırakacağım (veritabanı sütunu NULL kabul ediyor).
                messagebox.showwarning(
                    "Uyarı",
                    "Girilen saat tanımlı aralıkların dışında.\n"
                    "Ölçüm kaydedilecek fakat ortalama hesaplamasına katılmayacak."
                )

            # ---- veritabanına ekle
            db.add_blood_sugar_log(
                hasta_id,               # hasta
                olcum_dt,               # timestamp
                zaman_id,               # bulunabildiyse id, yoksa None
                seviye                  # seviye
            )
            db.close()

            messagebox.showinfo("Başarılı", "Kan şekeri kaydedildi.")
            win.destroy()

        except ValueError as ve:
            messagebox.showerror("Hata", str(ve))
        except Exception as ex:
            messagebox.showerror("Hata", f"Bir hata oluştu: {ex}")

    tk.Button(win, text="Kaydet", command=kaydet).pack(pady=14)
    win.mainloop()

# ------------------------------------------------------------------
# 2) HASTA ANA PENCERESİ
# ------------------------------------------------------------------
def run_patient(info: dict) -> None:
    root = tk.Tk()
    root.title("Hasta Paneli")
    root.geometry("400x300")

    tk.Label(
        root, text=f"Hoş geldiniz, {info['ad']} {info['soyad']}",
        font=("Arial", 14)
    ).pack(pady=12)

    tk.Button(
        root, text="Kan Şekeri Ekle",
        command=lambda: add_blood_sugar_ui(info["id"])
    ).pack(pady=10)

    tk.Button(
        root, text="Kan Şekeri Verilerini Görüntüle",
        command=lambda: show(info["id"])          # blood_sugar_ui.show()
    ).pack(pady=4)

    root.mainloop()
