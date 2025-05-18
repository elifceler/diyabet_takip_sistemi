import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from core.database import Database


def open_gecmis_oneriler_window(hasta_id: int) -> None:
    win = tk.Toplevel()
    win.title("Geçmiş Diyet ve Egzersiz Önerileri")
    win.geometry("670x500")
    win.resizable(False, False)

    tk.Label(
        win,
        text="Geçmiş Diyet ve Egzersiz Önerileri",
        font=("Arial", 14, "bold")
    ).pack(pady=10)

    notebook = ttk.Notebook(win)
    frm_diet = ttk.Frame(notebook)
    frm_exercise = ttk.Frame(notebook)
    notebook.add(frm_diet, text="Diyet Önerileri")
    notebook.add(frm_exercise, text="Egzersiz Önerileri")
    notebook.pack(fill="both", expand=True, padx=10, pady=10)

    def make_tree(parent: ttk.Frame) -> ttk.Treeview:
        cols = ("Tarih-Saat", "Öneri Türü")
        tv = ttk.Treeview(parent, columns=cols, show="headings", height=12)
        for c, w in zip(cols, (160, 440)):
            tv.heading(c, text=c)
            tv.column(c, width=w, anchor="center" if c == "Tarih-Saat" else "w")
        tv.pack(fill="both", expand=True)
        return tv

    tv_diet = make_tree(frm_diet)
    tv_exercise = make_tree(frm_exercise)

    db = Database(); db.connect()

    def load_data():
        tv_diet.delete(*tv_diet.get_children())
        tv_exercise.delete(*tv_exercise.get_children())

        diet_rows = db.fetch_all("""
            SELECT tarih, saat, dtr.ad
            FROM   diyet_takibi dt
            JOIN   diyet_turleri dtr ON dt.diyet_turu_id = dtr.id
            WHERE  dt.hasta_id = %s
            ORDER BY tarih DESC, saat DESC;
        """, (hasta_id,))

        for tarih, saat, diyet in diet_rows:
            tarih_str = f"{tarih.strftime('%d.%m.%Y')} {saat.strftime('%H:%M')}"
            tv_diet.insert("", "end", values=(tarih_str, diyet))

        exercise_rows = db.fetch_all("""
            SELECT tarih, saat, etr.ad
            FROM   egzersiz_takibi et
            JOIN   egzersiz_turleri etr ON et.egzersiz_turu_id = etr.id
            WHERE  et.hasta_id = %s
            ORDER BY tarih DESC, saat DESC;
        """, (hasta_id,))

        for tarih, saat, egzersiz in exercise_rows:
            tarih_str = f"{tarih.strftime('%d.%m.%Y')} {saat.strftime('%H:%M')}"
            tv_exercise.insert("", "end", values=(tarih_str, egzersiz))

    load_data()

    def delete_selected(tree: ttk.Treeview, table_name: str, field: str):
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("Uyarı", "Lütfen bir öneri seçin!")
            return

        values = tree.item(selected[0])["values"]
        tarih_saat, tur = values

        try:
            tarih_part, saat_part = tarih_saat.split()
            tarih_obj = datetime.strptime(tarih_part, "%d.%m.%Y").date()
            saat_obj = datetime.strptime(saat_part, "%H:%M").time()

            db.execute_query(f"""
                DELETE FROM {table_name}
                WHERE hasta_id = %s AND tarih = %s AND saat = %s
                      AND {field} = (
                          SELECT id FROM {field.replace('_id','_turleri')}
                          WHERE ad = %s
                      )
            """, (hasta_id, tarih_obj, saat_obj, tur))

            tree.delete(selected[0])
            messagebox.showinfo("Silindi", "Seçilen öneri başarıyla silindi.")

        except Exception as e:
            messagebox.showerror("Hata", f"Silme işlemi başarısız:\n{e}")

    ttk.Button(frm_diet, text="Seçili Diyeti Sil", command=lambda: delete_selected(tv_diet, "diyet_takibi", "diyet_turu_id")).pack(pady=5)
    ttk.Button(frm_exercise, text="Seçili Egzersizi Sil", command=lambda: delete_selected(tv_exercise, "egzersiz_takibi", "egzersiz_turu_id")).pack(pady=5)

    win.protocol("WM_DELETE_WINDOW", lambda: (db.close(), win.destroy()))