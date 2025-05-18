import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date
from core.database import Database

def open_pending_recommendations(hasta_id: int):
    win = tk.Toplevel()
    win.title("Uygulanmamış Öneriler")
    win.geometry("600x400")

    db = Database(); db.connect()

    # Diyet
    tk.Label(win, text="Not: Tarih sütunları doktorun öneriyi atadığı günü gösterir.", fg="gray").pack(pady=(4, 2))
    tk.Label(win, text="Uygulanmamış Diyetler", font=("Arial", 12, "bold")).pack(pady=6)
    diet_tree = ttk.Treeview(win, columns=("Tarih", "Diyet"), show="headings", height=5)
    for col in ("Tarih", "Diyet"):
        diet_tree.heading(col, text=col)
        diet_tree.column(col, width=200, anchor="center")
    diet_tree.pack()

    diyetler = db.fetch_all("""
        SELECT dt.id, dt.tarih, dtr.ad
        FROM diyet_takibi dt
        JOIN diyet_turleri dtr ON dt.diyet_turu_id = dtr.id
        WHERE dt.hasta_id = %s AND dt.durum = FALSE
        ORDER BY dt.tarih DESC;
    """, (hasta_id,))
    for id_, tarih, ad in diyetler:
        diet_tree.insert("", "end", iid=f"diyet_{id_}", values=(tarih.strftime("%d.%m.%Y"), ad))

    # Egzersiz
    tk.Label(win, text="Uygulanmamış Egzersizler", font=("Arial", 12, "bold")).pack(pady=6)
    ex_tree = ttk.Treeview(win, columns=("Tarih", "Egzersiz"), show="headings", height=5)
    for col in ("Tarih", "Egzersiz"):
        ex_tree.heading(col, text=col)
        ex_tree.column(col, width=200, anchor="center")
    ex_tree.pack()

    egzersizler = db.fetch_all("""
        SELECT et.id, et.tarih, etr.ad
        FROM egzersiz_takibi et
        JOIN egzersiz_turleri etr ON et.egzersiz_turu_id = etr.id
        WHERE et.hasta_id = %s AND et.durum = FALSE
        ORDER BY et.tarih DESC;
    """, (hasta_id,))
    for id_, tarih, ad in egzersizler:
        ex_tree.insert("", "end", iid=f"egzersiz_{id_}", values=(tarih.strftime("%d.%m.%Y"), ad))

    def isaretle():
        db = Database(); db.connect()
        selected_diyet = diet_tree.selection()
        selected_egz = ex_tree.selection()
        count = 0

        for iid in selected_diyet:
            id_ = int(iid.split("_")[1])
            tarih_row = db.fetch_one("SELECT tarih FROM diyet_takibi WHERE id = %s", (id_,))
            if tarih_row:
                tarih = tarih_row[0]
                # Aynı gün için zaten yapılmışsa atla
                var_mi = db.fetch_one("""
                    SELECT 1 FROM diyet_takibi
                    WHERE hasta_id = %s AND tarih = %s AND durum = TRUE
                """, (hasta_id, tarih))
                if var_mi:
                    messagebox.showinfo("Bilgi", f"{tarih.strftime('%d.%m.%Y')} için zaten diyet bildirimi yapılmış.")
                    continue

            db.execute_query("UPDATE diyet_takibi SET durum = TRUE WHERE id = %s", (id_,))
            diet_tree.delete(iid)
            count += 1

        for iid in selected_egz:
            id_ = int(iid.split("_")[1])
            tarih_row = db.fetch_one("SELECT tarih FROM egzersiz_takibi WHERE id = %s", (id_,))
            if tarih_row:
                tarih = tarih_row[0]
                var_mi = db.fetch_one("""
                    SELECT 1 FROM egzersiz_takibi
                    WHERE hasta_id = %s AND tarih = %s AND durum = TRUE
                """, (hasta_id, tarih))
                if var_mi:
                    messagebox.showinfo("Bilgi", f"{tarih.strftime('%d.%m.%Y')} için zaten egzersiz bildirimi yapılmış.")
                    continue

            db.execute_query("UPDATE egzersiz_takibi SET durum = TRUE WHERE id = %s", (id_,))
            ex_tree.delete(iid)
            count += 1

        db.close()

        if count > 0:
            messagebox.showinfo("Başarılı", f"{count} öneri 'uygulandı' olarak işaretlendi.")

    tk.Button(win, text="Seçilenleri Günlük Uygulandı Olarak Kaydet", command=isaretle, bg="green", fg="white").pack(pady=12)

    db.close()
