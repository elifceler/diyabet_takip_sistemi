# gui/tum_hasta_bilgileri_window.py
# ────────────────────────────────────────────────────────────────────────────────
"""
Doktorun tüm hastalarına ait, Öneri-Al penceresinden girilmiş
kan şekeri + belirtiler + diyet + egzersiz kayıtlarını satır satır listeler.

• Her ölçüm ayrı satırdır (1 hasta → n ölçüm satırı)
• Kan şekeri aralığı ve belirti filtresi uygulanabilir
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Any, Dict, List, Optional

from core.database import Database


# ────────────────────────────────────────────────────────────────────────────────
# Yardımcı – doktora bağlı tüm hastaların geçmiş verileri
# ────────────────────────────────────────────────────────────────────────────────
def _fetch_patients_for_doctor(db: Database, doctor_id: int) -> List[Dict[str, Any]]:
    """
    Doktora bağlı hastaların TÜM ÖNERİ-AL ölçümlerini getirir:
        • oneri_kan_sekeri        → tarih, saat, seviye
        • hasta_belirtileri       → seçili belirtiler
        • diyet_takibi / egzersiz_takibi → aynı güne ait son öneriler
    """
    rows = db.fetch_all(
        """
        SELECT
            h.tc_no,
            h.ad || ' ' || h.soyad               AS ad_soyad,
            TO_CHAR(h.dogum_tarihi,'DD.MM.YYYY') AS dob,
            h.cinsiyet,
            h.email,

            TO_CHAR(ks.tarih,'DD.MM.YYYY')       AS tarih,
            TO_CHAR(ks.saat ,'HH24:MI:SS')       AS saat,
            ks.seviye                            AS kan_sekeri,

            /* Hastanın o güne ait girilen belirtileri */
            COALESCE( (
                SELECT STRING_AGG(DISTINCT b.ad, ', ')
                FROM   hasta_belirtileri hb
                JOIN   belirtiler b ON b.id = hb.belirti_id
                WHERE  hb.hasta_id = h.id AND hb.tarih = ks.tarih
            ), '' ) AS belirtiler,

            /* Aynı gün için son diyet önerisi */
            COALESCE( (
                SELECT dtr.ad
                FROM   diyet_takibi dt
                JOIN   diyet_turleri dtr ON dtr.id = dt.diyet_turu_id
                WHERE  dt.hasta_id = h.id AND dt.tarih = ks.tarih
                ORDER  BY dt.saat DESC
                LIMIT  1
            ), '' ) AS diyet,

            /* Aynı gün için son egzersiz önerisi */
            COALESCE( (
                SELECT etr.ad
                FROM   egzersiz_takibi et
                JOIN   egzersiz_turleri etr ON etr.id = et.egzersiz_turu_id
                WHERE  et.hasta_id = h.id AND et.tarih = ks.tarih
                ORDER  BY et.saat DESC
                LIMIT  1
            ), '' ) AS egzersiz

        FROM   doktor_hasta       dh
        JOIN   kullanicilar       h  ON h.id = dh.hasta_id
        JOIN   oneri_kan_sekeri   ks ON ks.hasta_id = h.id       -- ← yeni tablo
        WHERE  dh.doktor_id = %s
        ORDER  BY h.ad, ks.tarih DESC, ks.saat DESC;
        """,
        (doctor_id,),
    )

    patients: List[Dict[str, Any]] = []
    for (
        tc, ad_soyad, dob, cinsiyet, email,
        tarih, saat, seviye, belirtiler, diyet, egzersiz
    ) in rows:
        patients.append(
            dict(
                tc=tc,
                ad_soyad=ad_soyad,
                dob=dob,
                cinsiyet=cinsiyet,
                email=email,
                tarih=f"{tarih} {saat}",
                seviye=seviye,
                belirtiler=belirtiler,
                diyet=diyet,
                egzersiz=egzersiz,
            )
        )
    return patients


# ────────────────────────────────────────────────────────────────────────────────
# Ana pencere
# ────────────────────────────────────────────────────────────────────────────────
def open_tum_hasta_bilgileri_window(doctor_id: int) -> None:
    win = tk.Toplevel()
    win.title("Tüm Hasta Bilgileri ve Filtreleme")
    win.geometry("1150x560")
    win.resizable(False, False)

    tk.Label(win, text="Tüm Hasta Bilgileri", font=("Arial", 16, "bold")).pack(pady=8)

    # ---------------- Filtre Alanı ----------------
    filt_frame = tk.Frame(win)
    filt_frame.pack(pady=4)

    # Kan şekeri aralığı
    tk.Label(filt_frame, text="Kan Şekeri  ≥").grid(row=0, column=0, pady=2)
    ent_min = tk.Entry(filt_frame, width=6)
    ent_min.grid(row=0, column=1, padx=4)
    tk.Label(filt_frame, text="≤").grid(row=0, column=2)
    ent_max = tk.Entry(filt_frame, width=6)
    ent_max.grid(row=0, column=3)

    # Belirti seçimi
    tk.Label(filt_frame, text="Belirti").grid(row=0, column=4, padx=12)
    cb_symptom = ttk.Combobox(filt_frame, width=22, state="readonly")
    cb_symptom.grid(row=0, column=5, padx=4)

    db = Database(); db.connect()
    symptom_rows = db.fetch_all("SELECT ad FROM belirtiler ORDER BY ad;")
    db.close()
    cb_symptom["values"] = ["Hepsi"] + [r[0] for r in symptom_rows]
    cb_symptom.current(0)

    # ---------------- Tablo ----------------
    columns = (
        "TC", "Ad Soyad", "Doğum Tarihi", "Cinsiyet", "E-posta",
        "Tarih", "Kan Şekeri", "Belirtiler", "Diyet", "Egzersiz"
    )
    tree = ttk.Treeview(win, columns=columns, show="headings", height=18)

    widths = (90, 160, 90, 70, 160, 130, 80, 200, 110, 110)
    justs  = ("center","w","center","center","w",
              "center","center","w","w","w")

    for col, w, j in zip(columns, widths, justs):
        tree.heading(col, text=col)
        tree.column(col, width=w, anchor=j)
    tree.pack(fill="both", expand=True, padx=10, pady=8)

    # --------- VERİ YÜKLEME / FİLTRELEME ---------
    patients_cache: List[Dict[str, Any]] = []

    def load_all_patients() -> None:
        nonlocal patients_cache
        db = Database(); db.connect()
        patients_cache = _fetch_patients_for_doctor(db, doctor_id)
        db.close()

    def populate_table(
        min_val: Optional[float] = None,
        max_val: Optional[float] = None,
        symptom: str = "Hepsi",
    ) -> None:
        tree.delete(*tree.get_children())
        for p in patients_cache:
            sev = p["seviye"]
            # Kan şekeri filtresi
            if min_val is not None and (sev is None or sev < min_val):
                continue
            if max_val is not None and (sev is None or sev > max_val):
                continue
            # Belirti filtresi
            if symptom != "Hepsi" and symptom.lower() not in p["belirtiler"].lower():
                continue

            tree.insert(
                "", "end",
                values=(
                    p["tc"], p["ad_soyad"], p["dob"], p["cinsiyet"], p["email"],
                    p["tarih"], p["seviye"], p["belirtiler"], p["diyet"], p["egzersiz"],
                )
            )

    # ----- Filtrele butonu -----
    def apply_filters() -> None:
        try:
            min_val = float(ent_min.get()) if ent_min.get().strip() else None
            max_val = float(ent_max.get()) if ent_max.get().strip() else None
            if min_val is not None and max_val is not None and min_val > max_val:
                raise ValueError("Min değer, max değerden büyük olamaz!")
        except ValueError as ve:
            messagebox.showerror("Hata", str(ve)); return

        populate_table(min_val, max_val, cb_symptom.get())

    tk.Button(filt_frame, text="Filtrele", command=apply_filters,
              bg="#2196F3", fg="white").grid(row=0, column=6, padx=8)

    # ----- Yenile butonu -----
    def manual_refresh():
        load_all_patients()
        apply_filters()

    tk.Button(filt_frame, text="Yenile", command=manual_refresh,
              bg="#4CAF50", fg="white").grid(row=0, column=7, padx=6)

    # ----- İlk yükleme -----
    load_all_patients()
    populate_table()

    win.focus_force()
    win.mainloop()
