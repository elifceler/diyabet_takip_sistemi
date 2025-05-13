import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from core.blood_sugar_ui import show


from core.database import Database
from core.user_management import add_patient, delete_patient
from core.validators import validate_tc, validate_email, validate_date

# ------------------------------------------------------------------
# 1) Doktora bağlı hastaları tabloya dolduran yardımcı fonksiyon
# ------------------------------------------------------------------
def load_patients(treeview: ttk.Treeview, doctor_id: int):
    treeview.delete(*treeview.get_children())

    db = Database(); db.connect()
    rows = db.fetch_all("""
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
    """, (doctor_id,))
    db.close()

    for r in rows:
        treeview.insert("", "end", iid=r[0], values=r[1:])



# ------------------------------------------------------------------
# 2) Doktor Ana Penceresi
# ------------------------------------------------------------------
def run_doctor(info: dict):
    """
    info = {'id': .., 'tc_no': .., 'ad': ..,
            'soyad': .., 'email': .., 'rol': 'doktor'}
    """
    root = tk.Tk()
    root.title("Doktor Paneli")
    root.geometry("760x520")

    # Başlık
    tk.Label(root, text=f"Dr. {info['ad']} {info['soyad']}", font=("Arial", 16)).pack(pady=10)

    # ------------------ HASTA TABLOSU ------------------
    columns = ("TC", "Ad Soyad", "E‑posta", "Cinsiyet", "Doğum Tarihi")
    tree = ttk.Treeview(root, columns=columns, show="headings", height=9)

    for col, width in zip(columns, (100, 180, 180, 80, 100)):
        tree.heading(col, text=col)
        tree.column(col, width=width, anchor="center")
    tree.pack(pady=8, fill="x", padx=15)

    load_patients(tree, info["id"])

    # ------------------ HASTA EKLEME FORMU ------------------
    form = tk.Frame(root)
    form.pack(pady=15)

    entries = {}

    def add_entry(label, show="", width=22):
        row = len(entries)
        tk.Label(form, text=label).grid(row=row, column=0, sticky="e", pady=2)
        e = tk.Entry(form, width=width, show=show)
        e.grid(row=row, column=1, padx=5)
        entries[label] = e

    # Metin kutuları
    for label in ("TC", "Ad", "Soyad", "Şifre", "E‑posta"):
        add_entry(label, show="*" if label == "Şifre" else "")

    # Cinsiyet combobox
    row = len(entries)
    tk.Label(form, text="Cinsiyet").grid(row=row, column=0, sticky="e", pady=2)
    gender_cb = ttk.Combobox(form, values=["Kadın", "Erkek", "Diğer"],
                             width=20, state="readonly")
    gender_cb.current(0)
    gender_cb.grid(row=row, column=1, padx=5)
    entries["Cinsiyet"] = gender_cb

    # Doğum tarihi
    add_entry("Doğum Tarihi (GG.AA.YYYY)")

    # --------------- Hasta Ekleme İşlevi ---------------
    def ekle():
        try:
            tc = entries["TC"].get().strip()
            ad = entries["Ad"].get().strip()
            soyad = entries["Soyad"].get().strip()
            pw = entries["Şifre"].get().strip()
            email = entries["E‑posta"].get().strip()
            cinsiyet = entries["Cinsiyet"].get()
            dob_raw = entries["Doğum Tarihi (GG.AA.YYYY)"].get().strip()

            # ---- BOŞ ALAN KONTROLÜ ----
            if not all([tc, ad, soyad, pw, email, dob_raw]):
                messagebox.showwarning("Uyarı", "Hiçbir alan boş bırakılamaz!")
                return

            # ---- BİÇİM DOĞRULAMALARI ----
            if not validate_tc(tc):
                messagebox.showerror("Hata", "TC Kimlik No 11 haneli rakamlardan oluşmalıdır.")
                return

            if not validate_email(email):
                messagebox.showerror("Hata", "E‑posta adresi geçerli formatta değil.")
                return

            dob = validate_date(dob_raw)
            if not dob:
                messagebox.showerror("Hata", "Doğum tarihi GG.AA.YYYY biçiminde olmalıdır.")
                return

            # ---- VERİTABANINA EKLE ----
            add_patient(info["id"], tc, ad, soyad, pw, email, dob, cinsiyet)
            messagebox.showinfo("Başarılı", f"{ad} {soyad} eklendi")
            load_patients(tree, info["id"])

            # Formu temizle
            for widget in entries.values():
                if isinstance(widget, tk.Entry):
                    widget.delete(0, tk.END)
            gender_cb.current(0)

        except ValueError:
            messagebox.showerror("Hata", "Doğum tarihi GG.AA.YYYY formatında olmalı")
        except Exception as ex:
            messagebox.showerror("Hata", str(ex))

    tk.Button(root, text="Hasta Ekle", command=ekle).pack(pady=6)

    def sil():
        selected = tree.selection()

        if not selected:
            messagebox.showwarning("Uyarı", "Lütfen bir hasta seçin!")
            return

        # Seçilen hasta ID
        patient_id = selected[0]

        # Silme onayı
        confirm = messagebox.askyesno("Onay", "Bu hastayı silmek istediğinize emin misiniz?")
        if confirm:
            try:
                delete_patient(patient_id)
                load_patients(tree, info["id"])
                messagebox.showinfo("Başarılı", "Hasta silindi.")
            except Exception as ex:
                messagebox.showerror("Hata", str(ex))

    tk.Button(root, text="Hasta Sil", command=sil).pack(pady=6)

    def view_blood_sugar():
        sel = tree.selection()
        if not sel:
            messagebox.showwarning("Uyarı", "Lütfen bir hasta seçin!")
            return
        show(int(sel[0]))

    tk.Button(root, text="Kan Şekeri Verilerini Görüntüle", command=view_blood_sugar).pack(pady=10)

    root.mainloop()
