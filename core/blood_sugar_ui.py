import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from core.database import Database

def show(hasta_id: int) -> None:
    """Hasta için kan şekeri verilerini ve insülin önerisini gösterir."""
    # ---------- Pencere ----------
    win = tk.Toplevel()
    win.title("Kan Şekeri Verileri ve İnsülin Önerisi")
    win.geometry("600x500")

    tk.Label(
        win,
        text="Kan Şekeri Verileri ve İnsülin Önerisi",
        font=("Arial", 14)
    ).pack(pady=10)

    # ---------- Ölçüm Tablosu ----------
    columns = ("Tarih", "Saat", "Seviye (mg/dL)")
    tree = ttk.Treeview(win, columns=columns, show="headings", height=10)
    for col, w in zip(columns, (150, 100, 150)):
        tree.heading(col, text=col)
        tree.column(col, width=w, anchor="center")
    tree.pack(pady=10, fill="both", expand=True)

    # ---------- İnsülin Önerisi Alanı ----------
    insulin_frame = tk.Frame(win)
    insulin_frame.pack(pady=10, fill="x")

    tk.Label(insulin_frame, text="İnsülin Önerisi:", font=("Arial", 12)).pack()
    insulin_text = tk.Text(
        insulin_frame, width=60, height=5, wrap="word", state="disabled"
    )
    insulin_text.pack(pady=5)

    # ---------- Verileri Çek ----------
    db = Database()
    db.connect()
    blood_sugar_logs = db.fetch_all(
        """
        SELECT olcum_zamani, seviye
        FROM kan_sekeri_olcumleri
        WHERE hasta_id = %s
        ORDER BY olcum_zamani DESC;
        """,
        (hasta_id,),
    )
    db.close()

    # Ölçümleri bloklara ayır
    measurements = {
        "Sabah": None,   # 07:00‑08:59
        "Öğle":  None,   # 12:00‑13:59
        "İkindi": None,  # 15:00‑16:59
        "Akşam": None,   # 18:00‑19:59
        "Gece":  None,   # 22:00‑23:59
    }

    for olcum_zamani, seviye in blood_sugar_logs:
        tarih = olcum_zamani.strftime("%d.%m.%Y")
        saat  = olcum_zamani.strftime("%H:%M:%S")
        tree.insert("", "end", values=(tarih, saat, seviye))

        hour = olcum_zamani.hour
        if 7  <= hour < 9:
            measurements["Sabah"]  = seviye
        elif 12 <= hour < 14:
            measurements["Öğle"]   = seviye
        elif 15 <= hour < 17:
            measurements["İkindi"] = seviye
        elif 18 <= hour < 20:
            measurements["Akşam"]  = seviye
        elif 22 <= hour < 24:
            measurements["Gece"]   = seviye

    # ---------- Ortalama & Doz Hesabı ----------
    def calculate_insulin_dose() -> None:
        valid = [v for v in measurements.values() if v is not None]

        insulin_text.config(state="normal")
        insulin_text.delete("1.0", "end")

        # < 3 ölçüm → güvenilir değil
        if len(valid) < 3:
            insulin_text.insert(
                "1.0",
                "Yetersiz veri! Ortalama hesaplaması güvenilir değildir."
            )
            insulin_text.config(state="disabled")
            return

        # Eksik ölçüm uyarısı
        if len(valid) < 5:
            messagebox.showwarning(
                "Uyarı",
                "Ölçüm eksik! Ortalama alınırken bazı ölçümler hesaba katılmadı."
            )

        avg = sum(valid) / len(valid)

        # İnsülin dozu
        if   avg < 70:
            dose = "Yok (Hipoglisemi)"
        elif avg <= 110:
            dose = "Yok (Normal)"
        elif avg <= 150:
            dose = "1 ml"
        elif avg <= 200:
            dose = "2 ml"
        else:
            dose = "3 ml"

        insulin_text.insert(
            "1.0",
            f"Ortalama Kan Şekeri: {avg:.2f} mg/dL\nİnsülin Önerisi: {dose}"
        )
        insulin_text.config(state="disabled")

    # ---------- Hesapla Butonu ----------
    tk.Button(
        insulin_frame,
        text="İnsülin Önerisi Hesapla",
        command=calculate_insulin_dose
    ).pack(pady=5)

    win.mainloop()

def view_patient_blood_sugar_logs(hasta_id):
    """Hasta için kan şekeri verilerini listeleyen arayüz"""

    win = tk.Toplevel()
    win.title("Kan Şekeri Verileri")
    win.geometry("600x400")

    # Başlık
    tk.Label(win, text="Kan Şekeri Verileri", font=("Arial", 14)).pack(pady=10)

    # Kan şekeri verilerini listelemek için Treeview
    columns = ("Tarih", "Saat", "Seviye (mg/dL)")
    tree = ttk.Treeview(win, columns=columns, show="headings", height=15)

    for col, width in zip(columns, (150, 100, 150)):
        tree.heading(col, text=col)
        tree.column(col, width=width, anchor="center")

    tree.pack(pady=10, fill="both", expand=True)

    # Verileri Veritabanından Çekme
    db = Database();
    db.connect()
    blood_sugar_logs = db.fetch_all("""
        SELECT olcum_zamani, seviye 
        FROM kan_sekeri_olcumleri 
        WHERE hasta_id = %s 
        ORDER BY olcum_zamani DESC;
    """, (hasta_id,))
    db.close()

    # Verileri tabloya ekleme
    for log in blood_sugar_logs:
        olcum_zamani, seviye = log
        tarih = olcum_zamani.strftime("%d.%m.%Y")
        saat = olcum_zamani.strftime("%H:%M:%S")
        tree.insert("", "end", values=(tarih, saat, seviye))

