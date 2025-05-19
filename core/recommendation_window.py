# core/recommendation_window.py
# ────────────────────────────────────────────────────────────────────────────────
"""
Doktorun seçili hasta için kan şekeri + belirtilere göre
diyet ve egzersiz önerisi kaydedebildiği pencere.

Kaydedilen tablolar
-------------------
1. oneri_kan_sekeri   → kan şekeri, tarih-saat, hasta_ad
2. hasta_belirtileri  → seçilen belirtiler (tarih bazlı)
3. diyet_takibi       → durum=False
4. egzersiz_takibi    → durum=False
"""
from __future__ import annotations

import tkinter as tk
from tkinter import messagebox
from datetime import datetime, date, time
from typing import Dict, List, Tuple

from core.database import Database
from core.oneriler import get_recommendations


# ────────────────────────────────────────────────────────────────────────────────
def open_recommendation_window(hasta_id: int) -> None:  # noqa: C901
    """Doktor panelinden ‘Öneri Al’ tıklandığında bu pencere açılır."""
    # ——— Pencere ——————————————————————————————————————————
    win = tk.Toplevel()
    win.title("Diyet ve Egzersiz Önerisi")
    win.geometry("420x650")
    win.resizable(False, False)

    # ----- Kan şekeri girişi ----------------------------------------------------
    tk.Label(win, text="Kan Şekeri (mg/dL)", font=("Arial", 12, "bold")
             ).pack(pady=(14, 4))
    ent_sugar = tk.Entry(win, width=12, justify="center"); ent_sugar.pack()

    # ----- Tarih girişi ---------------------------------------------------------
    tk.Label(win, text="Tarih (GG.AA.YYYY)", font=("Arial", 12, "bold")
             ).pack(pady=(18, 4))
    ent_date = tk.Entry(win, width=20, justify="center")
    ent_date.insert(0, datetime.now().strftime("%d.%m.%Y")); ent_date.pack()

    # ----- Belirtiler -----------------------------------------------------------
    tk.Label(win, text="Belirtiler", font=("Arial", 12, "bold")
             ).pack(pady=(18, 6))
    frame_chk = tk.Frame(win, height=220)
    frame_chk.pack(fill="both", expand=True, padx=10)
    frame_chk.pack_propagate(False)

    symptom_vars: Dict[int, Tuple[str, tk.BooleanVar]] = {}

    # Belirtileri DB’den çek
    try:
        db = Database(); db.connect()
        rows: List = db.fetch_all("SELECT id, ad FROM belirtiler ORDER BY ad;")
        db.close()
    except Exception as exc:
        messagebox.showerror("Hata", f"Belirtiler alınamadı:\n{exc}"); win.destroy(); return

    if not rows:
        tk.Label(frame_chk, text="⚠️  Belirti listesi boş!", fg="red").pack()
    else:
        for idx, row in enumerate(rows):
            bid, ad = (row["id"], row["ad"]) if isinstance(row, dict) else row
            var = tk.BooleanVar(value=False)
            tk.Checkbutton(frame_chk, text=ad, anchor="w",
                           variable=var
                           ).grid(row=idx // 2, column=idx % 2,
                                  sticky="w", padx=4, pady=2)
            symptom_vars[bid] = (ad, var)

    # ---------------------------------------------------------------------------
    def handle_recommend() -> None:
        # Kan şekeri
        try:
            ks_val = float(ent_sugar.get().strip())
        except ValueError:
            messagebox.showerror("Hata", "Geçerli bir kan şekeri değeri girin."); return

        # Seçili belirtiler
        sel_ids   = [bid for bid, (_, v) in symptom_vars.items() if v.get()]
        sel_names = [name for (_id, (name, v)) in symptom_vars.items() if v.get()]
        if not sel_ids:
            messagebox.showwarning("Uyarı", "En az bir belirti seçmelisiniz."); return

        # Tarih
        try:
            tarih_sql: date = datetime.strptime(ent_date.get().strip(), "%d.%m.%Y").date()
        except ValueError:
            messagebox.showerror("Hata", "Tarih GG.AA.YYYY biçiminde olmalı."); return
        saat_sql: time = datetime.now().time()

        # Öneri
        rec = get_recommendations(ks_val, sel_names)
        if rec is None:
            messagebox.showerror("Kural Yok",
                                 "Bu kombinasyon için kural tanımlı değil."); return
        diet, exercise = rec

        # ── DB işlemleri ───────────────────────────────────────────────
        db = Database(); db.connect()

        ad, soyad, tc = db.fetch_one(
            "SELECT ad, soyad, tc_no FROM kullanicilar WHERE id=%s;", (hasta_id,))
        tam_ad = f"{ad} {soyad}"

        # 0) Kan şekeri → oneri_kan_sekeri
        db.execute_query(
            """
            INSERT INTO oneri_kan_sekeri
            (hasta_id, hasta_ad, tarih, saat, seviye)
            VALUES (%s, %s, %s, %s, %s);
            """,
            (hasta_id, tam_ad, tarih_sql, saat_sql, ks_val)
        )

        # 1) Belirtiler → hasta_belirtileri
        for bid in sel_ids:
            db.execute_query(
                """
                INSERT INTO hasta_belirtileri (hasta_id, belirti_id, tarih)
                VALUES (%s, %s, %s)
                ON CONFLICT DO NOTHING;
                """,
                (hasta_id, bid, tarih_sql)
            )

        # 2) Diyet / egzersiz türlerini ekle
        db.execute_query(
            "INSERT INTO diyet_turleri(ad,aciklama) VALUES(%s,%s) ON CONFLICT DO NOTHING;",
            (diet, f"Otomatik öneri {datetime.now():%d.%m.%Y}")
        )
        db.execute_query(
            "INSERT INTO egzersiz_turleri(ad,aciklama) VALUES(%s,%s) ON CONFLICT DO NOTHING;",
            (exercise, f"Otomatik öneri {datetime.now():%d.%m.%Y}")
        )
        diet_id = db.fetch_one("SELECT id FROM diyet_turleri WHERE ad=%s;", (diet,))[0]
        ex_id   = db.fetch_one("SELECT id FROM egzersiz_turleri WHERE ad=%s;", (exercise,))[0]

        # 3) Takip tabloları
        db.execute_query(
            """
            INSERT INTO diyet_takibi
            (hasta_id,tarih,saat,durum,diyet_turu_id,hasta_ad,hasta_tc)
            VALUES (%s,%s,%s,FALSE,%s,%s,%s);
            """,
            (hasta_id, tarih_sql, saat_sql, diet_id, tam_ad, tc)
        )
        db.execute_query(
            """
            INSERT INTO egzersiz_takibi
            (hasta_id,tarih,saat,durum,egzersiz_turu_id,hasta_ad,hasta_tc)
            VALUES (%s,%s,%s,FALSE,%s,%s,%s);
            """,
            (hasta_id, tarih_sql, saat_sql, ex_id, tam_ad, tc)
        )

        db.close()
        messagebox.showinfo("Öneriler", f"✅ Diyet: {diet}\n✅ Egzersiz: {exercise}")
        win.destroy()

    # — Kaydet düğmesi
    tk.Button(win, text="Öneriyi Hesapla ve Kaydet",
              command=handle_recommend,
              bg="#4CAF50", fg="white",
              padx=12, pady=4).pack(pady=24)
