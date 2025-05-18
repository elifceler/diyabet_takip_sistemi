# core/recommendation_window.py
import tkinter as tk
from tkinter import messagebox
from datetime import datetime

from core.database    import Database
from core.oneriler    import get_recommendations


def open_recommendation_window(hasta_id: int) -> None:
    """ Doktor – seçili hasta için öneri penceresini açar """

    # ----------------- Pencere -----------------
    win = tk.Toplevel()
    win.title("Diyet ve Egzersiz Önerisi")
    win.geometry("420x580")
    win.resizable(False, False)

    # ----------------- Kan şekeri girişi -----------------
    tk.Label(
        win, text="Kan Şekeri (mg/dL)", font=("Arial", 12, "bold")
    ).pack(pady=(12, 4))
    sugar_entry = tk.Entry(win, width=12, justify="center")
    sugar_entry.pack()

    # --- Tarih girişi ---
    tk.Label(win, text="Tarih (GG.AA.YYYY)", font=("Arial", 12, "bold")).pack(pady=(16, 4))
    date_entry = tk.Entry(win, width=20, justify="center")
    date_entry.insert(0, datetime.now().strftime("%d.%m.%Y"))
    date_entry.pack()

    # ----------------- Belirtiler listesi -----------------
    tk.Label(
        win, text="Belirtiler", font=("Arial", 12, "bold")
    ).pack(pady=(16, 6))

    checkbox_frame = tk.Frame(win)
    checkbox_frame.pack(fill="both", expand=True, padx=10)

    belirtiler_vars: dict[str, tk.BooleanVar] = {}

    try:
        db = Database(); db.connect()
        # Sadece ad sütununu alıyoruz
        rows = db.fetch_all("SELECT ad FROM belirtiler ORDER BY ad;")
        db.close()

        if not rows:
            tk.Label(
                checkbox_frame,
                text="⚠️  Belirti listesi boş!",
                fg="red"
            ).pack()
        else:
            # 2-sütunlu grid yerleşimi
            for i, (belirti,) in enumerate(rows):
                var = tk.BooleanVar(value=False)
                chk = tk.Checkbutton(
                    checkbox_frame, text=belirti, variable=var, anchor="w"
                )
                chk.grid(row=i // 2, column=i % 2, sticky="w", padx=4, pady=2)
                belirtiler_vars[belirti] = var
    except Exception as e:
        messagebox.showerror(
            "Hata",
            f"Belirtiler alınırken sorun oluştu:\n{e}"
        )
        win.destroy()
        return

    # ----------------- Öner / Kaydet işlemi -----------------
    def create_recommendations() -> None:
        try:
            # -- Giriş doğrulamaları
            sugar = float(sugar_entry.get().strip())
        except ValueError:
            messagebox.showerror("Hata", "Geçerli bir kan şekeri değeri girin.")
            return

        selected_symptoms = [
            b for b, v in belirtiler_vars.items() if v.get()
        ]
        if not selected_symptoms:
            messagebox.showwarning("Uyarı", "En az bir belirti seçmelisiniz.")
            return

        # -- Öneri hesapla
        diet, exercise = get_recommendations(sugar, selected_symptoms)

        # -- Zaman damgası
        try:
            tarih_str = datetime.strptime(date_entry.get().strip(), "%d.%m.%Y").date()
        except ValueError:
            messagebox.showerror("Hata", "Tarih formatı GG.AA.YYYY olmalı.")
            return

        saat_str = datetime.now().time()

        db = Database(); db.connect()

        # --- Hasta bilgileri (ad soyad & TC) -----------------
        hasta = db.fetch_one(
            "SELECT ad, soyad, tc_no FROM kullanicilar WHERE id = %s;",
            (hasta_id,)
        )
        if not hasta:
            db.close()
            messagebox.showerror("Hata", "Hasta bilgisi alınamadı.")
            return
        hasta_ad, hasta_soyad, hasta_tc = hasta
        tam_ad = f"{hasta_ad} {hasta_soyad}"

        # --- Diyet & egzersiz türlerini (varsa ekleme) -------
        db.execute_query(
            """
            INSERT INTO diyet_turleri (ad, aciklama)
            VALUES (%s, %s)
            ON CONFLICT (ad) DO NOTHING;
            """,
            (diet, f"Otomatik öneri {tarih_str.strftime('%d.%m.%Y')}")

        )

        db.execute_query(
            """
            INSERT INTO egzersiz_turleri (ad, aciklama)
            VALUES (%s, %s)
            ON CONFLICT (ad) DO NOTHING;
            """,
            (exercise, f"Otomatik öneri {tarih_str.strftime('%d.%m.%Y')}")
        )

        # Tür ID’lerini çek
        diet_id = db.fetch_one(
            "SELECT id FROM diyet_turleri WHERE ad = %s;", (diet,)
        )[0]
        ex_id   = db.fetch_one(
            "SELECT id FROM egzersiz_turleri WHERE ad = %s;", (exercise,)
        )[0]

        # --- Takip tablolarına ekle --------------------------
        db.execute_query(
            """
            INSERT INTO diyet_takibi
            (hasta_id, tarih, saat, durum, diyet_turu_id,
             hasta_ad, hasta_tc)
            VALUES (%s, %s, %s, FALSE, %s, %s, %s);
            """,
            (hasta_id, tarih_str, saat_str, diet_id, tam_ad, hasta_tc)
        )

        db.execute_query(
            """
            INSERT INTO egzersiz_takibi
            (hasta_id, tarih, saat, durum, egzersiz_turu_id,
             hasta_ad, hasta_tc)
            VALUES (%s, %s, %s, FALSE, %s, %s, %s);
            """,
            (hasta_id, tarih_str, saat_str, ex_id, tam_ad, hasta_tc)
        )

        db.close()

        # -- Doktora göster
        messagebox.showinfo(
            "Öneriler",
            f"✅ Diyet: {diet}\n✅ Egzersiz: {exercise}"
        )
        win.destroy()   # pencereyi kapat

    # ----------------- Buton -----------------
    tk.Button(
        win,
        text="Öneriyi Hesapla ve Kaydet",
        command=create_recommendations,
        bg="#4CAF50", fg="white",
        padx=10, pady=4
    ).pack(pady=18)

