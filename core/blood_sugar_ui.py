import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from core.database import Database

def show(hasta_id: int) -> None:
    win = tk.Toplevel()
    win.title("Kan Şekeri Verileri ve İnsülin Önerisi")
    win.geometry("600x600")

    tk.Label(win, text="Kan Şekeri Verileri", font=("Arial", 14)).pack(pady=10)

    # --- Ölçüm Tablosu ---
    columns = ("Tarih", "Saat", "Seviye (mg/dL)")
    tree = ttk.Treeview(win, columns=columns, show="headings", height=10)
    for col, w in zip(columns, (150, 100, 150)):
        tree.heading(col, text=col)
        tree.column(col, width=w, anchor="center")
    tree.pack(pady=10, fill="both", expand=True)

    db = Database()
    db.connect()

    db.check_first_time_measurement_alert(hasta_id)

    # Ölçüm verileri
    logs = db.fetch_all("""
        SELECT olcum_zamani, seviye
        FROM kan_sekeri_olcumleri
        WHERE hasta_id = %s
        ORDER BY olcum_zamani DESC;
    """, (hasta_id,))
    for olcum_zamani, seviye in logs:
        tarih = olcum_zamani.strftime("%d.%m.%Y")
        saat = olcum_zamani.strftime("%H:%M:%S")
        tree.insert("", "end", values=(tarih, saat, seviye))

    # --- İnsülin Önerileri ---
    tk.Label(win, text="İnsülin Önerileri", font=("Arial", 14)).pack(pady=10)

    tk.Label(win, text="Tarihe göre filtrele (GG.AA.YYYY):").pack()
    filter_entry = tk.Entry(win, width=20, justify="center")
    filter_entry.pack(pady=4)


    dose_cols = ("Tarih", "Ortalama", "Doz (ml)")
    dose_tv = ttk.Treeview(win, columns=dose_cols, show="headings", height=6)
    for col, w in zip(dose_cols, (150, 150, 100)):
        dose_tv.heading(col, text=col)
        dose_tv.column(col, width=w, anchor="center")
    dose_tv.pack(pady=5, fill="x")

    dose_rows = db.get_insulin_suggestions(hasta_id)
    db.close()

    for tarih, ort, doz in dose_rows:
        doz_str = "Yetersiz" if doz == -1 else f"{doz} ml"
        dose_tv.insert("", "end", values=(tarih.strftime("%d.%m.%Y"), f"{ort:.2f}", doz_str))

    def on_dose_double_click(event):
        selected = dose_tv.selection()
        if not selected:
            return
        item = dose_tv.item(selected[0])
        tarih_str = item["values"][0]  # "13.05.2025"
        show_day_details(tarih_str, hasta_id)

    dose_tv.bind("<Double-1>", on_dose_double_click)

    def delete_selected_measurement():
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("Uyarı", "Lütfen silmek için bir ölçüm seçin.")
            return
        confirm = messagebox.askyesno("Silme Onayı", "Seçilen ölçümü silmek istiyor musunuz?")
        if not confirm:
            return

        item = tree.item(selected[0])
        tarih_str, saat_str, _ = item["values"]
        ts = datetime.strptime(f"{tarih_str} {saat_str}", "%d.%m.%Y %H:%M:%S")

        db = Database()
        db.connect()
        db.execute_query("""
            DELETE FROM kan_sekeri_olcumleri
            WHERE hasta_id = %s AND olcum_zamani = %s
        """, (hasta_id, ts))
        db.close()
        tree.delete(selected[0])
        messagebox.showinfo("Başarılı", "Ölçüm silindi.")

    tk.Button(win, text="Seçili Ölçümü Sil", command=delete_selected_measurement).pack(pady=4)

    alert_frame = tk.Frame(win)
    alert_frame.pack(pady=10, fill="x")

    tk.Label(alert_frame, text="Uyarılar", font=("Arial", 12)).pack()

    alert_box = tk.Text(alert_frame, width=70, height=6, wrap="word", state="normal")
    alert_box.pack(pady=5)

    db = Database()
    db.connect()
    alerts = db.get_alerts(hasta_id)
    db.close()

    if not alerts:
        alert_box.insert("1.0", "Kayıtlı bir uyarı bulunamadı.")
    else:
        for _, tarih, uyari_tipi, mesaj, _ in alerts:
            alert_box.insert("end", f"{tarih} | {uyari_tipi}: {mesaj}\n")

    alert_box.config(state="disabled")

    def filtrele_insulin():
        tarih_str = filter_entry.get().strip()
        try:
            hedef_tarih = datetime.strptime(tarih_str, "%d.%m.%Y").date()
        except ValueError:
            messagebox.showerror("Hata", "Tarih biçimi GG.AA.YYYY olmalı.")
            return

        for i in dose_tv.get_children():
            dose_tv.delete(i)

        db = Database(); db.connect()
        dose_rows = db.get_insulin_suggestions(hasta_id)
        db.close()

        for tarih, ort, doz in dose_rows:
            if tarih == hedef_tarih:
                doz_str = "Yetersiz" if doz == -1 else f"{doz} ml"
                dose_tv.insert("", "end", values=(tarih.strftime("%d.%m.%Y"), f"{ort:.2f}", doz_str))


    tk.Button(win, text="Filtrele", command=filtrele_insulin, bg="#007ACC", fg="white").pack(pady=4)

    win.mainloop()

    def show_day_details(tarih_str, hasta_id):
        """
        Belirli bir güne ait saat + seviye detaylarını gösterir.
        """
        win = tk.Toplevel()
        win.title(f"{tarih_str} Ölçüm Detayları")
        win.geometry("400x400")

        tk.Label(win, text=f"{tarih_str} Günlük Ölçümler", font=("Arial", 14)).pack(pady=10)

        columns = ("Saat", "Seviye (mg/dL)")
        tree = ttk.Treeview(win, columns=columns, show="headings", height=15)
        for col, w in zip(columns, (150, 150)):
            tree.heading(col, text=col)
            tree.column(col, width=w, anchor="center")
        tree.pack(pady=10, fill="both", expand=True)

        db = Database()
        db.connect()
        rows = db.fetch_all("""
            SELECT olcum_zamani, seviye
            FROM kan_sekeri_olcumleri
            WHERE hasta_id = %s AND DATE(olcum_zamani) = %s
            ORDER BY olcum_zamani;
        """, (hasta_id, datetime.strptime(tarih_str, "%d.%m.%Y").date()))
        db.close()

        for olcum_zamani, seviye in rows:
            saat = olcum_zamani.strftime("%H:%M:%S")
            tree.insert("", "end", values=(saat, seviye))
