# core/recommendation_window.py
# ────────────────────────────────────────────────────────────────────────────────
"""
Doktorun seçili hasta için kan şekeri + belirtilere göre
diyet ve egzersiz önerisi girebildiği pencere.

Bu sürüm, önceki iki varyanttaki farkları birleştirir ve aşağıdaki
iyileştirmeleri içerir:

• Belirtiler veritabanından dinamik çekilir.
• Doktor tarih alanını (GG.AA.YYYY) manuel girebilir;
  varsayılan olarak bugünün tarihiyle doldurulur.
• Öneri, :pyfunc:`core.oneriler.get_recommendations` üzerinden hesaplanır.
• Diyet / egzersiz türleri yoksa eklenir, ardından *takip* tablolarına işlenir.
• Oluşturulan kayıtlar *durum = FALSE* (hasta henüz uygulamadı) olarak eklenir.
"""
from __future__ import annotations

import tkinter as tk
from tkinter import messagebox
from datetime import datetime
from typing import Dict, List

from core.database import Database
from core.oneriler import get_recommendations


# ────────────────────────────────────────────────────────────────────────────────
def open_recommendation_window(hasta_id: int) -> None:  # noqa: C901  (GUI fonksiyonu)
    """Doktor → seçili *hasta* için öneri penceresini açar."""

    # ——— Pencere ————————————————————————————————————————————————
    win = tk.Toplevel()
    win.title("Diyet ve Egzersiz Önerisi")
    win.geometry("420x620")
    win.resizable(False, False)

    # ——— Kan şekeri girişi ————————————————————————————————————
    tk.Label(
        win,
        text="Kan Şekeri (mg/dL)",
        font=("Arial", 12, "bold"),
    ).pack(pady=(12, 4))
    ent_sugar = tk.Entry(win, width=12, justify="center")
    ent_sugar.pack()

    # ——— Tarih girişi —————————————————————————————————————————
    tk.Label(
        win,
        text="Tarih (GG.AA.YYYY)",
        font=("Arial", 12, "bold"),
    ).pack(pady=(16, 4))
    ent_date = tk.Entry(win, width=20, justify="center")
    ent_date.insert(0, datetime.now().strftime("%d.%m.%Y"))
    ent_date.pack()

    # ——— Belirtiler listesi ——————————————————————————————————
    tk.Label(
        win,
        text="Belirtiler",
        font=("Arial", 12, "bold"),
    ).pack(pady=(16, 6))

    frame_chk = tk.Frame(win)
    frame_chk.pack(fill="both", expand=True, padx=10)

    symptom_vars: Dict[str, tk.BooleanVar] = {}

    # Veritabanından belirtileri çek
    try:
        db = Database(); db.connect()
        rows: List = db.fetch_all("SELECT ad FROM belirtiler ORDER BY ad;")
        db.close()
    except Exception as exc:
        messagebox.showerror("Hata", f"Belirtiler alınamadı:\n{exc}")
        win.destroy(); return

    if not rows:
        tk.Label(frame_chk, text="⚠️  Belirti listesi boş!", fg="red").pack()
    else:
        for idx, row in enumerate(rows):
            belirti = row[0] if not isinstance(row, dict) else row["ad"]
            var = tk.BooleanVar(value=False)
            chk = tk.Checkbutton(frame_chk, text=belirti, variable=var, anchor="w")
            chk.grid(row=idx // 2, column=idx % 2, sticky="w", padx=4, pady=2)
            symptom_vars[belirti] = var

    # ——— Öneriyi oluştur / kaydet ——————————————————————————
    def handle_recommend() -> None:
        # Kan şekeri doğrulama
        try:
            ks_value = float(ent_sugar.get().strip())
        except ValueError:
            messagebox.showerror("Hata", "Geçerli bir kan şekeri değeri girin.")
            return

        selected = [s for s, var in symptom_vars.items() if var.get()]
        if not selected:
            messagebox.showwarning("Uyarı", "En az bir belirti seçmelisiniz.")
            return

        # Tarih doğrulama
        try:
            tarih_sql = datetime.strptime(ent_date.get().strip(), "%d.%m.%Y").date()
        except ValueError:
            messagebox.showerror("Hata", "Tarih formatı GG.AA.YYYY olmalı.")
            return

        # Öneriyi hesapla
        rec = get_recommendations(ks_value, selected)
        if rec is None:
            messagebox.showerror(
                "Kural Eşleşmedi",
                "Bu kan şekeri / belirti kombinasyonu için tanımlı kural yok.",
            )
            return
        diet, exercise = rec

        now = datetime.now()
        saat_sql = now.time()  # TIME  HH:MM:SS

        # ——— Veritabanı işlemleri —————————————————————————
        db = Database(); db.connect()

        # Hasta bilgileri
        hasta = db.fetch_one(
            "SELECT ad, soyad, tc_no FROM kullanicilar WHERE id = %s;",
            (hasta_id,),
        )
        if not hasta:
            db.close(); messagebox.showerror("Hata", "Hasta bilgisi alınamadı."); return
        ad, soyad, tc_no = hasta
        tam_ad = f"{ad} {soyad}"

        # Diyet & egzersiz türleri ekle (varsa skip)
        db.execute_query(
            """
            INSERT INTO diyet_turleri (ad, aciklama)
            VALUES (%s, %s)
            ON CONFLICT (ad) DO NOTHING;
            """,
            (diet, f"Otomatik öneri {now:%d.%m.%Y}"),
        )
        db.execute_query(
            """
            INSERT INTO egzersiz_turleri (ad, aciklama)
            VALUES (%s, %s)
            ON CONFLICT (ad) DO NOTHING;
            """,
            (exercise, f"Otomatik öneri {now:%d.%m.%Y}"),
        )

        # Tür ID'leri
        diet_id = db.fetch_one("SELECT id FROM diyet_turleri WHERE ad = %s;", (diet,))[0]
        ex_id   = db.fetch_one("SELECT id FROM egzersiz_turleri WHERE ad = %s;", (exercise,))[0]

        # Takip tablolarına yaz (durum=False ⇒ hasta henüz uygulamadı)
        db.execute_query(
            """
            INSERT INTO diyet_takibi
            (hasta_id, tarih, saat, durum, diyet_turu_id,
             hasta_ad, hasta_tc)
            VALUES (%s, %s, %s, FALSE, %s, %s, %s);
            """,
            (hasta_id, tarih_sql, saat_sql, diet_id, tam_ad, tc_no),
        )
        db.execute_query(
            """
            INSERT INTO egzersiz_takibi
            (hasta_id, tarih, saat, durum, egzersiz_turu_id,
             hasta_ad, hasta_tc)
            VALUES (%s, %s, %s, FALSE, %s, %s, %s);
            """,
            (hasta_id, tarih_sql, saat_sql, ex_id, tam_ad, tc_no),
        )

        db.close()

        # Bilgi mesajı + pencereyi kapat
        messagebox.showinfo("Öneriler", f"✅ Diyet: {diet}\n✅ Egzersiz: {exercise}")
        win.destroy()

    # ——— Buton ————————————————————————————————————————————
    tk.Button(
        win,
        text="Öneriyi Hesapla ve Kaydet",
        command=handle_recommend,
        bg="#4CAF50",
        fg="white",
        padx=12,
        pady=4,
    ).pack(pady=20)
