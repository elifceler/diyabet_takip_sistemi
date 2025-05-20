# gui/doctor_window.py
# ────────────────────────────────────────────────────────────────────────────────
import tkinter as tk
from tkinter import ttk, messagebox
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt

from core.database import Database
from core.user_management import add_patient, delete_patient
from core.validators import validate_tc, validate_email, validate_date
from core.blood_sugar_ui import show                                # kan şekeri geçmişi
from core.recommendation_window import open_recommendation_window   # diyet/egzersiz önerisi
from core.gecmis_oneriler_window import open_gecmis_oneriler_window
from gui.patient_window import show_progress
from core.graph_utils import show_combined_graph
from core.tum_hasta_bilgileri_window import open_tum_hasta_bilgileri_window
from gui.kisi_bilgisi_window import open_kisi_bilgisi_window
from gui.profil_window import upload_profile_picture
# ────────────────────────────────────────────────────────────────────────────────


# ------------------------------------------------------------------
# HASTA LİSTESİNİ YENİDEN YÜKLE
# ------------------------------------------------------------------
def load_patients(tree: ttk.Treeview, doctor_id: int) -> None:
    tree.delete(*tree.get_children())

    db = Database(); db.connect()
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
    root = tk.Tk()
    root.title("Doktor Paneli")
    root.geometry("880x780")
    root.resizable(False, False)

    # ------------------ BAŞLIK ------------------
    tk.Label(root, text=f"Dr. {info['ad']} {info['soyad']}",
             font=("Arial", 16, "bold")).pack(pady=10)

    # ------------------ HASTA TABLOSU ------------------
    columns = ("TC", "Ad Soyad", "E-posta", "Cinsiyet", "Doğum Tarihi")
    tree = ttk.Treeview(root, columns=columns, show="headings", height=8)

    for col, w in zip(columns, (110, 180, 190, 80, 110)):
        tree.heading(col, text=col)
        tree.column(col, width=w, anchor="center")
    tree.pack(padx=15, fill="x")

    load_patients(tree, info["id"])

    # ------------------ HASTA EKLEME FORMU ------------------
    form = tk.Frame(root); form.pack(pady=12)
    entries: dict[str, tk.Entry | ttk.Combobox] = {}

    def add_entry(label: str, show: str = "", width: int = 24) -> None:
        row = len(entries)
        tk.Label(form, text=label).grid(row=row, column=0, sticky="e", pady=2)
        e = tk.Entry(form, width=width, show=show)
        e.grid(row=row, column=1, padx=6)
        entries[label] = e

    for lbl in ("TC", "Ad", "Soyad", "Şifre", "E-posta"):
        add_entry(lbl, show="*" if lbl == "Şifre" else "")

    # Cinsiyet
    row = len(entries)
    tk.Label(form, text="Cinsiyet").grid(row=row, column=0, sticky="e", pady=2)
    gender_cb = ttk.Combobox(form, values=["Kadın", "Erkek", "Diğer"],
                             width=22, state="readonly")
    gender_cb.current(0)
    gender_cb.grid(row=row, column=1, padx=6)
    entries["Cinsiyet"] = gender_cb

    # Doğum tarihi
    add_entry("Doğum Tarihi (GG.AA.YYYY)")

    # ------------------ İŞLEVSEL FONKSİYONLAR ------------------
    def add_patient_ui() -> None:
        try:
            tc = entries["TC"].get().strip()
            ad = entries["Ad"].get().strip()
            soyad = entries["Soyad"].get().strip()
            password = entries["Şifre"].get().strip()
            email = entries["E-posta"].get().strip()
            cinsiyet = entries["Cinsiyet"].get()
            dob_raw = entries["Doğum Tarihi (GG.AA.YYYY)"].get().strip()

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

            add_patient(info["id"], tc, ad, soyad, password, email, dob, cinsiyet)
            load_patients(tree, info["id"])

            from core.email_utils import send_login_email
            try:
                send_login_email(email, password, tc)
                messagebox.showinfo("Bilgi", "Hasta eklendi ve şifre e-posta adresine gönderildi.")
            except Exception as e:
                messagebox.showwarning("E-posta Hatası",
                                       f"Hasta kaydedildi ancak e-posta gönderilemedi.\n{e}")

            for w in entries.values():
                if isinstance(w, tk.Entry):
                    w.delete(0, tk.END)
            gender_cb.current(0)

        except Exception as ex:
            messagebox.showerror("Hata", str(ex))

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

    def view_blood_sugar() -> None:
        sel = tree.selection()
        if not sel:
            messagebox.showwarning("Uyarı", "Önce bir hasta seçin!")
            return
        show(int(sel[0]))

    def view_alerts() -> None:
        sel = tree.selection()
        if not sel:
            messagebox.showwarning("Uyarı", "Önce bir hasta seçin!")
            return
        hasta_id = int(sel[0])
        db = Database(); db.connect()
        db.generate_all_doctor_alerts(hasta_id)
        db.check_first_time_measurement_alert(hasta_id)
        alerts = db.get_doctor_alerts(hasta_id)
        db.close()

        alert_win = tk.Toplevel(); alert_win.title("Uyarılar"); alert_win.geometry("600x400")
        tk.Label(alert_win, text="Hastaya Ait Doktor Uyarıları",
                 font=("Arial", 14)).pack(pady=10)
        txt = tk.Text(alert_win, width=80, height=20, wrap="word")
        txt.pack(padx=10, pady=10, fill="both", expand=True)
        if not alerts:
            txt.insert("1.0", "Bu hastaya ait kayıtlı uyarı bulunamadı.")
        else:
            for _, tarih, tipi, mesaj, _ in alerts:
                tarih_str = tarih.strftime("%d.%m.%Y") if not isinstance(tarih, str) else tarih
                txt.insert("end", f"{tarih_str} | {tipi}: {mesaj}\n")
        txt.config(state="disabled")

    def open_recommendation() -> None:
        sel = tree.selection()
        if not sel:
            messagebox.showwarning("Uyarı", "Önce bir hasta seçin!")
            return
        open_recommendation_window(int(sel[0]))

    def view_past_recommendations() -> None:
        sel = tree.selection()
        if not sel:
            messagebox.showwarning("Uyarı", "Lütfen bir hasta seçin!")
            return
        open_gecmis_oneriler_window(int(sel[0]))

    def open_all_patients() -> None:
        open_tum_hasta_bilgileri_window(info["id"])

    def view_progress_for_selected_patient() -> None:
        sel = tree.selection()
        if not sel:
            messagebox.showwarning("Uyarı", "Lütfen bir hasta seçin.")
            return
        show_progress(int(sel[0]))

    def show_patient_adherence_graph(hasta_id: int):
        db = Database(); db.connect()
        total_diet = db.fetch_one("SELECT COUNT(*) FROM diyet_takibi WHERE hasta_id=%s",
                                  (hasta_id,))[0]
        done_diet  = db.fetch_one(
            "SELECT COUNT(*) FROM diyet_takibi WHERE hasta_id=%s AND durum=TRUE",
            (hasta_id,))[0]
        total_ex   = db.fetch_one("SELECT COUNT(*) FROM egzersiz_takibi WHERE hasta_id=%s",
                                  (hasta_id,))[0]
        done_ex    = db.fetch_one(
            "SELECT COUNT(*) FROM egzersiz_takibi WHERE hasta_id=%s AND durum=TRUE",
            (hasta_id,))[0]
        db.close()

        diet_percent = round((done_diet / total_diet) * 100, 2) if total_diet else 0
        ex_percent   = round((done_ex   / total_ex)   * 100, 2) if total_ex   else 0

        win = tk.Toplevel(); win.title("Uygulama Oranı"); win.geometry("600x400")
        fig, ax = plt.subplots(figsize=(6, 4))
        ax.bar(["Diyet", "Egzersiz"], [diet_percent, ex_percent],
               color=["#4CAF50", "#2196F3"])
        ax.set_ylim(0, 100); ax.set_ylabel("Uygulanma Oranı (%)")
        ax.set_title("Diyet ve Egzersiz Önerilerinin Uygulanma Oranı")
        for i, val in enumerate([diet_percent, ex_percent]):
            ax.text(i, val + 2, f"{val}%", ha="center", fontweight="bold")
        fig.tight_layout()
        FigureCanvasTkAgg(fig, master=win).draw()

    def view_adherence_graph():
        sel = tree.selection()
        if not sel:
            messagebox.showwarning("Uyarı", "Lütfen bir hasta seçin!")
            return
        show_patient_adherence_graph(int(sel[0]))

    def view_relationship_graph() -> None:
        sel = tree.selection()
        if not sel:
            messagebox.showwarning("Uyarı", "Lütfen bir hasta seçin!")
            return
        show_combined_graph(int(sel[0]))

    # ------------------------------------------------------------------
    # KOMUT BUTONLARI – 2 sütunlu, kompakt
    # ------------------------------------------------------------------
    btn_frame = tk.Frame(root); btn_frame.pack(pady=6)
    BTN = dict(width=12, pady=2)

    # Satır 0
    tk.Button(btn_frame, text="Hasta Ekle", bg="#4CAF50", fg="white",
              command=add_patient_ui, **BTN).grid(row=0, column=0, padx=4)
    tk.Button(btn_frame, text="Hasta Sil",  bg="#F44336", fg="white",
              command=delete_patient_ui, **BTN).grid(row=0, column=1, padx=4)

    # Satır 1
    tk.Button(btn_frame, text="Kan Şekeri Verileri",
              command=view_blood_sugar, **BTN).grid(row=1, column=0, padx=4)
    tk.Button(btn_frame, text="Uyarıları Gör",
              command=view_alerts, **BTN).grid(row=1, column=1, padx=4)

    # Satır 2
    tk.Button(btn_frame, text="Öneri Al", bg="#2196F3", fg="white",
              command=open_recommendation, **BTN).grid(row=2, column=0, padx=4)
    tk.Button(btn_frame, text="Geçmiş Öneriler",
              command=view_past_recommendations, **BTN).grid(row=2, column=1, padx=4)

    # Satır 3 – tek buton
    tk.Button(btn_frame, text="Tüm Hasta Bilgileri", bg="#673AB7", fg="white",
              command=open_all_patients, **BTN).grid(row=3, column=0, columnspan=2, pady=(4,2))

    # Satır 4
    tk.Button(btn_frame, text="Öneri Uygulama", bg="#FFC107",
              command=view_progress_for_selected_patient, **BTN).grid(row=4, column=0, padx=4)
    tk.Button(btn_frame, text="Uygulama Grafiği", bg="#8E44AD", fg="white",
              command=view_adherence_graph, **BTN).grid(row=4, column=1, padx=4)

    # Satır 5 – tek buton
    tk.Button(btn_frame, text="Kan Şekeri İlişki", bg="#03A9F4", fg="white",
              command=view_relationship_graph, **BTN).grid(row=5, column=0, columnspan=2, pady=(4,0))

    # ------------------ GERİ DÖN ------------------
    tk.Button(root, text="Geri Dön",
              command=lambda: back_to_login(root),
              bg="black", fg="white").pack(pady=10)

    tk.Button(btn_frame,
              text="Kişi Bilgisi",
              command=lambda: open_kisi_bilgisi_window(info["id"]),
              bg="#9C27B0", fg="white",
              **BTN
              ).grid(row=6, column=0, columnspan=2, pady=(6, 0))

    root.mainloop()


def back_to_login(window):
    window.destroy()
    from main import run_entry
    run_entry()
