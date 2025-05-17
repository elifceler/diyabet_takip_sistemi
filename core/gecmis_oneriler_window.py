import tkinter as tk
from tkinter import ttk
from datetime import datetime

from core.database import Database


def open_gecmis_oneriler_window(hasta_id: int) -> None:
    """Seçilen hasta için geçmiş diyet / egzersiz önerilerini gösterir."""
    win = tk.Toplevel()
    win.title("Geçmiş Diyet ve Egzersiz Önerileri")
    win.geometry("650x460")
    win.resizable(False, False)

    tk.Label(
        win,
        text="Geçmiş Diyet ve Egzersiz Önerileri",
        font=("Arial", 14, "bold")
    ).pack(pady=10)

    # ---------- Sekmeler ----------
    notebook = ttk.Notebook(win)
    frm_diet     = ttk.Frame(notebook)
    frm_exercise = ttk.Frame(notebook)
    notebook.add(frm_diet,     text="Diyet Önerileri")
    notebook.add(frm_exercise, text="Egzersiz Önerileri")
    notebook.pack(fill="both", expand=True, padx=10, pady=10)

    # ---------- Ortak tablo kurucu ----------
    def make_tree(parent: ttk.Frame) -> ttk.Treeview:
        cols = ("Tarih-Saat", "Öneri Türü")
        tv = ttk.Treeview(parent, columns=cols, show="headings", height=12)

        for c, w in zip(cols, (160, 440)):
            tv.heading(c, text=c)
            tv.column(c, width=w, anchor="center" if c == "Tarih-Saat" else "w")

        tv.pack(fill="both", expand=True)
        return tv

    tv_diet     = make_tree(frm_diet)
    tv_exercise = make_tree(frm_exercise)

    # ---------- Veritabanından verileri çek ----------
    db = Database(); db.connect()

    diet_rows = db.fetch_all(
        """
        SELECT dt.tarih, dtr.ad
        FROM   diyet_takibi dt
        JOIN   diyet_turleri dtr ON dt.diyet_turu_id = dtr.id
        WHERE  dt.hasta_id = %s
        ORDER  BY dt.tarih DESC;
        """,
        (hasta_id,)
    )

    for tarih, diyet in diet_rows:
        tarih_str = tarih.strftime("%d.%m.%Y %H:%M") \
                    if isinstance(tarih, datetime) else str(tarih)
        tv_diet.insert("", "end", values=(tarih_str, diyet))

    exercise_rows = db.fetch_all(
        """
        SELECT et.tarih, etr.ad
        FROM   egzersiz_takibi et
        JOIN   egzersiz_turleri etr ON et.egzersiz_turu_id = etr.id
        WHERE  et.hasta_id = %s
        ORDER  BY et.tarih DESC;
        """,
        (hasta_id,)
    )

    for tarih, egzersiz in exercise_rows:
        tarih_str = tarih.strftime("%d.%m.%Y %H:%M") \
                    if isinstance(tarih, datetime) else str(tarih)
        tv_exercise.insert("", "end", values=(tarih_str, egzersiz))

    db.close()
