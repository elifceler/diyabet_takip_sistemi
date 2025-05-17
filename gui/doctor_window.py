# gui/doctor_window.py
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date            # şimdilik yalnızca future-proof için
                                      # (view_alerts içinde tarih formatı gerekirse)

from core.database import Database
from core.user_management import add_patient, delete_patient
from core.validators import validate_tc, validate_email, validate_date
from core.blood_sugar_ui import show                         # kan şekeri geçmişi
from core.recommendation_window import open_recommendation_window  # diyet/egzersiz önerisi
from core.gecmis_oneriler_window import open_gecmis_oneriler_window

# ------------------------------------------------------------------
# HASTA LİSTESİNİ YENİDEN YÜKLE
# ------------------------------------------------------------------
def load_patients(tree: ttk.Treeview, doctor_id: int) -> None:
    """Doktora bağlı hastaları TreeView’e doldurur."""
    tree.delete(*tree.get_children())

    db = Database()
    db.connect()
    rows = db.fetch_all(
        """
        SELECT h.id,
               h.tc_no,
               h.ad || ' ' || h.soyad,
               h.email,
               h.cinsiyet,
               TO_CHAR(h.dogum_tarihi,'DD.MM.YYYY')
        FROM doktor_hasta dh
        JOIN kullanicilar h ON h.id = dh.hasta_id
        WHERE dh.doktor_id = %s
        ORDER BY h.ad;
        """,
        (doctor_id,),
    )
    db.close()

    for r in rows:
        tree.insert("", "end", iid=r[0], values=r[1:])


# ------------------------------------------------------------------
# DOKTOR ANA PENCERESİ
# ------------------------------------------------------------------
def run_doctor(info: dict) -> None:
    """
    info = {
        'id'   : doktorun id’si,
        'ad'   : ad,
        'soyad': soyad,
        'email': e-posta,
        'rol'  : 'doktor'
    }
    """
    root = tk.Tk()
    root.title("Doktor Paneli")
    root.geometry("780x660")
    root.resizable(False, False)

    # ------------------ BAŞLIK ------------------
    tk.Label(
        root,
        text=f"Dr. {info['ad']} {info['soyad']}",
        font=("Arial", 16, "bold"),
    ).pack(pady=10)

    # ------------------ HASTA TABLOSU ------------------
    columns = ("TC", "Ad Soyad", "E-posta", "Cinsiyet", "Doğum Tarihi")
    tree = ttk.Treeview(root, columns=columns, show="headings", height=8)

    for col, w in zip(columns, (110, 180, 190, 80, 110)):
        tree.heading(col, text=col)
        tree.column(col, width=w, anchor="center")
    tree.pack(padx=15, fill="x")

    load_patients(tree, info["id"])

    # ------------------ HASTA EKLEME FORMU ------------------
    form = tk.Frame(root)
    form.pack(pady=12)

    entries: dict[str, tk.Entry | ttk.Combobox] = {}

    def add_entry(label: str, show: str = "", width: int = 24) -> None:
        """Form’a satır ekler ve Entry/Combobox referansını entries sözlüğüne koyar."""
        row = len(entries)
        tk.Label(form, text=label).grid(row=row, column=0, sticky="e", pady=2)
        e = tk.Entry(form, width=width, show=show)
        e.grid(row=row, column=1, padx=6)
        entries[label] = e

    # Metin kutuları
    for lbl in ("TC", "Ad", "Soyad", "Şifre", "E-posta"):
        add_entry(lbl, show="*" if lbl == "Şifre" else "")

    # Cinsiyet seçimi
    row = len(entries)
    tk.Label(form, text="Cinsiyet").grid(row=row, column=0, sticky="e", pady=2)
    gender_cb = ttk.Combobox(
        form, values=["Kadın", "Erkek", "Diğer"], width=22, state="readonly"
    )
    gender_cb.current(0)
    gender_cb.grid(row=row, column=1, padx=6)
    entries["Cinsiyet"] = gender_cb

    # Doğum tarihi
    add_entry("Doğum Tarihi (GG.AA.YYYY)")

    # ------------------ HASTA EKLE ------------------
    def add_patient_ui() -> None:
        try:
            tc = entries["TC"].get().strip()
            ad = entries["Ad"].get().strip()
            soyad = entries["Soyad"].get().strip()
            password = entries["Şifre"].get().strip()
            email = entries["E-posta"].get().strip()
            cinsiyet = entries["Cinsiyet"].get()
            dob_raw = entries["Doğum Tarihi (GG.AA.YYYY)"].get().strip()

            # ---- doğrulamalar
            if not all([tc, ad, soyad, password, email, dob_raw]):
                messagebox.showwarning("Uyarı", "Lütfen tüm alanları doldurun!")
                return
            if not validate_tc(tc):
                messagebox.showerror("Hata", "TC Kimlik No 11 haneli rakamlardan oluşmalıdır.")
                return
            if not validate_email(email):
                messagebox.showerror("Hata", "E-posta adresi geçerli formatta değil.")
                return
            dob = validate_date(dob_raw)
            if not dob:
                messagebox.showerror("Hata", "Doğum tarihi GG.AA.YYYY biçiminde olmalı.")
                return

            # ---- veritabanına ekle
            add_patient(info["id"], tc, ad, soyad, password, email, dob, cinsiyet)
            load_patients(tree, info["id"])
            messagebox.showinfo("Başarılı", f"{ad} {soyad} eklendi.")

            # formu temizle
            for w in entries.values():
                if isinstance(w, tk.Entry):
                    w.delete(0, tk.END)
            gender_cb.current(0)

        except Exception as ex:
            messagebox.showerror("Hata", str(ex))

    tk.Button(
        root, text="Hasta Ekle", command=add_patient_ui, bg="#4CAF50", fg="white"
    ).pack(pady=4)

    # ------------------ HASTA SİL ------------------
    def delete_patient_ui() -> None:
        sel = tree.selection()
        if not sel:
            messagebox.showwarning("Uyarı", "Önce bir hasta seçin!")
            return
        pid = sel[0]
        if messagebox.askyesno("Onay", "Seçilen hastayı silmek istiyor musunuz?"):
            try:
                delete_patient(pid)
                load_patients(tree, info["id"])
                messagebox.showinfo("Silindi", "Hasta kaydı silindi.")
            except Exception as ex:
                messagebox.showerror("Hata", str(ex))

    tk.Button(
        root, text="Hasta Sil", command=delete_patient_ui, bg="#f44336", fg="white"
    ).pack(pady=4)

    # ------------------ KAN ŞEKERİ GEÇMİŞİ ------------------
    def view_blood_sugar() -> None:
        sel = tree.selection()
        if not sel:
            messagebox.showwarning("Uyarı", "Önce bir hasta seçin!")
            return
        show(int(sel[0]))

    tk.Button(
        root, text="Kan Şekeri Verilerini Görüntüle", command=view_blood_sugar
    ).pack(pady=4)

    # ------------------ UYARILARI GÖRÜNTÜLE ------------------
    def view_alerts() -> None:
        sel = tree.selection()
        if not sel:
            messagebox.showwarning("Uyarı", "Önce bir hasta seçin!")
            return

        hasta_id = int(sel[0])

        db = Database()
        db.connect()
        # Güncel uyarıları üret / ilk ölçüm kontrolü
        db.generate_all_doctor_alerts(hasta_id)
        db.check_first_time_measurement_alert(hasta_id)
        alerts = db.get_doctor_alerts(hasta_id)
        db.close()

        alert_win = tk.Toplevel()
        alert_win.title("Uyarılar")
        alert_win.geometry("600x400")

        tk.Label(alert_win, text="Hastaya Ait Doktor Uyarıları", font=("Arial", 14)).pack(
            pady=10
        )

        alert_box = tk.Text(alert_win, width=80, height=20, wrap="word", state="normal")
        alert_box.pack(padx=10, pady=10, fill="both", expand=True)

        if not alerts:
            alert_box.insert("1.0", "Bu hastaya ait kayıtlı uyarı bulunamadı.")
        else:
            for _, tarih, tipi, mesaj, _ in alerts:
                # tarih sütunu DATE/TIMESTAMP veya str gelebilir
                tarih_str = (
                    tarih.strftime("%d.%m.%Y") if not isinstance(tarih, str) else tarih
                )
                alert_box.insert("end", f"{tarih_str} | {tipi}: {mesaj}\n")

        alert_box.config(state="disabled")

    tk.Button(root, text="Uyarıları Görüntüle", command=view_alerts).pack(pady=4)

    # ------------------ ÖNERİ AL ------------------
    def open_recommendation() -> None:
        sel = tree.selection()
        if not sel:
            messagebox.showwarning("Uyarı", "Önce bir hasta seçin!")
            return
        open_recommendation_window(int(sel[0]))

    tk.Button(
        root, text="Öneri Al", command=open_recommendation, bg="#2196F3", fg="white"
    ).pack(pady=6)

    def view_past_recommendations():
        sel = tree.selection()
        if not sel:
            messagebox.showwarning("Uyarı", "Lütfen bir hasta seçin!")
            return
        open_gecmis_oneriler_window(int(sel[0]))

    tk.Button(
        root,
        text="Geçmiş Önerileri Gör",
        command=view_past_recommendations,
        bg="gray",
        fg="white"
    ).pack(pady=4)  # <—  pack çağrısı doğrudan run_doctor içindeyse görünür




    root.mainloop()
