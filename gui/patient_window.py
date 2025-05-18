# gui/patient_window.py
import tkinter as tk
from tkinter import messagebox
from datetime import datetime
from core.database import Database
from core.blood_sugar_ui import show   # ölçüm‑liste & insülin penceresi
from gui.onerileri_uygula_window import open_pending_recommendations
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


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

            # Aynı gün ve aynı zaman aralığında ölçüm var mı kontrolü
            if zaman_id is not None:
                var_mi = db.fetch_one("""
                    SELECT id FROM kan_sekeri_olcumleri
                    WHERE hasta_id = %s AND DATE(olcum_zamani) = %s AND olcum_zamani_id = %s
                """, (hasta_id, olcum_dt.date(), zaman_id))

                if var_mi:
                    db.close()
                    messagebox.showerror("Hata", "Bu zaman aralığına ait bir ölçüm zaten mevcut.")
                    return

            if zaman_id is None:
                # Saat aralığı dışı: kaydet → ortalamaya katılmasın
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

            db.check_insulin_data_alert(hasta_id, olcum_dt.date())
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

    tk.Button(
        root, text="Diyet / Egzersiz Önerilerini Uygula",
        command=lambda: open_pending_recommendations(info["id"])
    ).pack(pady=4)

    tk.Button(
        root, text="Öneri Uygulama Durumu",
        command=lambda: show_progress(info["id"])
    ).pack(pady=4)

    tk.Button(
        root, text="Kan Şekeri Grafiğini Göster",
        command=lambda: show_blood_sugar_graph(info["id"])
    ).pack(pady=4)

    tk.Button(
        root, text="Geri Dön",
        command=lambda: back_to_login(root)
    ).pack(pady=10)


    root.mainloop()

def show_progress(hasta_id: int):
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    import tkinter as tk
    from core.database import Database

    db = Database()
    db.connect()
    diyet_oran, egzersiz_oran = db.get_recommendation_progress(hasta_id)
    db.close()

    win = tk.Toplevel()
    win.title("Öneri Uygulama Yüzdesi")
    win.geometry("500x400")
    win.resizable(False, False)

    fig, ax = plt.subplots(figsize=(5, 3.5))
    kategoriler = ['Diyet', 'Egzersiz']
    oranlar = [diyet_oran, egzersiz_oran]
    colors = ['#4CAF50', '#2196F3']

    bars = ax.bar(kategoriler, oranlar, color=colors)
    ax.set_ylim(0, 100)
    ax.set_ylabel("Uygulama Oranı (%)")
    ax.set_title("Diyet ve Egzersiz Uygulama Yüzdesi")

    for bar, oran in zip(bars, oranlar):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2.0, height + 3, f"{oran:.0f}%", ha='center', va='bottom', fontsize=10)

    canvas = FigureCanvasTkAgg(fig, master=win)
    canvas.draw()
    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    tk.Button(win, text="Kapat", command=win.destroy).pack(pady=6)

def show_blood_sugar_graph(hasta_id: int):
    db = Database()
    db.connect()
    data = db.get_insulin_averages_for_graph(hasta_id)
    db.close()

    if not data:
        messagebox.showinfo("Bilgi", "Gösterilecek kan şekeri verisi bulunamadı.")
        return

    tarih_list = [row[0].strftime("%d.%m.%Y") for row in data]
    ortalama_list = [float(row[1]) for row in data]

    win = tk.Toplevel()
    win.title("Günlük Kan Şekeri Grafiği")
    win.geometry("600x400")

    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot(tarih_list, ortalama_list, marker='o', linestyle='-', color='blue')
    ax.set_title("Günlük Ortalama Kan Şekeri Seviyesi")
    ax.set_xlabel("Tarih")
    ax.set_ylabel("Ortalama Seviye (mg/dL)")
    ax.tick_params(axis='x', rotation=45)

    canvas = FigureCanvasTkAgg(fig, master=win)
    canvas.draw()
    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    tk.Button(win, text="Kapat", command=win.destroy).pack(pady=6)

def back_to_login(window):
    window.destroy()  # Hasta panelini kapat
    from main import run_entry  # Giriş ekranını yeniden başlat
    run_entry()
