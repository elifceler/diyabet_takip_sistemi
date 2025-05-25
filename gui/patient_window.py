"""
Refactored patient window module with modern ttk widgets, consistent styling,
centralized layout helpers and colourful buttons. All original functionality
remains intact, but the main window now launches maximised and displays each
action's UI on the right-hand side of the same screen instead of separate
pop-up windows. Pop‑up açan eski modüller de, geçici bir Toplevel yamasıyla
gömülü olarak aynı panelde gösterilir.
"""
import os
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from core.database import Database
from core.blood_sugar_ui import show  # Ölçüm‑liste & insülin penceresi
from gui.onerileri_uygula_window import open_pending_recommendations
from gui.kisi_bilgisi_window import open_kisi_bilgisi_window


# ---------------------------------------------------------------------------
# ==========  Genel Yardımcı Fonksiyonlar  ==================================
# ---------------------------------------------------------------------------

def center_window(win: tk.Toplevel | tk.Tk, w: int, h: int) -> None:
    """Ekranın ortasına yerleştirir."""
    win.update_idletasks()
    x = (win.winfo_screenwidth() - w) // 2
    y = (win.winfo_screenheight() - h) // 2
    win.geometry(f"{w}x{h}+{x}+{y}")


def create_style() -> ttk.Style:
    """Uygulama genelinde kullanılacak ttk stillerini tanımlar."""
    style = ttk.Style()

    try:
        style.theme_use("clam")  # platform‑bağımsız tutarlı görünüm
    except tk.TclError:
        pass

    style.configure("TFrame", background="#F8F9FA")
    style.configure("TLabel", background="#F8F9FA", font=("Segoe UI", 10))
    style.configure("Title.TLabel", font=("Segoe UI", 14, "bold"))

    # Kaydet & benzeri önemli buton stili
    style.configure(
        "Accent.TButton",
        font=("Segoe UI", 10, "bold"),
        foreground="white",
        background="#2196F3",
        padding=6,
    )
    style.map("Accent.TButton", background=[("active", "#1976D2")])

    return style


# ---------------------------------------------------------------------------
# ========== 1) ÖLÇÜM EKLEME ARAYÜZÜ =======================================
# ---------------------------------------------------------------------------

def add_blood_sugar_ui(hasta_id: int, parent: tk.Widget | None = None) -> None:
    """Kan şekeri ekleme formunu *parent* içinde (varsa) veya pop‑up olarak gösterir."""

    # Pop‑up mı gömülü mü?
    if parent is None:
        win = tk.Toplevel()
        win.title("Kan Şekeri Ekle")
        center_window(win, 360, 400)
        create_style()
        container = win
    else:
        for child in parent.winfo_children():
            child.destroy()
        container = parent

    frm = ttk.Frame(container, padding=20)
    frm.pack(fill="both", expand=True)

    ttk.Label(frm, text="Kan Şekeri Ekle", style="Title.TLabel").pack(pady=(0, 12))

    # ------------------------------------------------------------------
    # Giriş alanı yardımcı fonksiyonu
    # ------------------------------------------------------------------

    def add_row(lbl: str, default: str = "") -> tk.Entry:
        row = ttk.Frame(frm)
        row.pack(fill="x", pady=4)
        ttk.Label(row, text=lbl, width=20, anchor="w").pack(side="left")
        ent = ttk.Entry(row, width=20)
        ent.pack(side="right", fill="x", expand=True)
        if default:
            ent.insert(0, default)
        return ent

    now = datetime.now()
    seviye_entry = add_row("Seviye (mg/dL)")
    tarih_entry = add_row("Tarih (GG.AA.YYYY)", now.strftime("%d.%m.%Y"))
    saat_entry = add_row("Saat (HH:MM)", now.strftime("%H:%M"))

    # ------------------------------------------------------------------
    # Kaydet işlevi
    # ------------------------------------------------------------------

    def kaydet() -> None:
        seviye_str = seviye_entry.get().strip()
        tarih_str = tarih_entry.get().strip()
        saat_str = saat_entry.get().strip()

        if not (seviye_str and tarih_str and saat_str):
            messagebox.showwarning("Uyarı", "Lütfen tüm alanları doldurun!", parent=container)
            return

        try:
            # Seviye doğrulama
            if not seviye_str.isdigit():
                raise ValueError("Seviye sadece sayılardan oluşmalıdır.")
            seviye = int(seviye_str)
            if not 0 <= seviye <= 500:
                raise ValueError("Seviye 0-500 aralığında olmalıdır.")

            # Tarih & saat doğrulama
            try:
                ts_str = f"{tarih_str} {saat_str}"
                olcum_dt = datetime.strptime(ts_str, "%d.%m.%Y %H:%M")
            except ValueError:
                raise ValueError("Tarih/Saat biçimi GG.AA.YYYY ve HH:MM olmalıdır.")

            db = Database();
            db.connect()

            zaman_kayitlari = db.fetch_all(
                "SELECT id, saat_baslangic, saat_bitis FROM olcum_zamanlari"
            )
            zaman_id: int | None = None

            for z_id, bas_str, bit_str in zaman_kayitlari:
                bas = datetime.strptime(str(bas_str), "%H:%M:%S").time()
                bit = datetime.strptime(str(bit_str), "%H:%M:%S").time()
                if bas <= olcum_dt.time() <= bit:
                    zaman_id = z_id
                    break

            # Aynı gün aynı zaman aralığı kontrolü
            if zaman_id is not None:
                var_mi = db.fetch_one(
                    """
                    SELECT id FROM kan_sekeri_olcumleri
                    WHERE hasta_id = %s AND DATE(olcum_zamani) = %s AND olcum_zamani_id = %s
                    """,
                    (hasta_id, olcum_dt.date(), zaman_id),
                )
                if var_mi:
                    db.close()
                    messagebox.showerror(
                        "Hata", "Bu zaman aralığına ait bir ölçüm zaten mevcut.", parent=container
                    )
                    return

            if zaman_id is None:
                messagebox.showwarning(
                    "Uyarı",
                    "Girilen saat tanımlı aralıkların dışında.\n"
                    "Ölçüm kaydedilecek fakat ortalama hesaplamasına katılmayacak.",
                    parent=container,
                )

            # Veritabanına ekle
            db.add_blood_sugar_log(hasta_id, olcum_dt, zaman_id, seviye)
            db.check_insulin_data_alert(hasta_id, olcum_dt.date())
            db.close()

            messagebox.showinfo("Başarılı", "Kan şekeri kaydedildi.", parent=container)

            # Pop‑up ise pencereyi kapat; gömülü ise sadece alanı temizle
            if isinstance(container, tk.Toplevel):
                container.destroy()
            else:
                seviye_entry.delete(0, tk.END)

        except ValueError as ve:
            messagebox.showerror("Hata", str(ve), parent=container)
        except Exception as ex:
            messagebox.showerror("Hata", f"Bir hata oluştu: {ex}", parent=container)

    ttk.Button(frm, text="Kaydet", style="Accent.TButton", command=kaydet).pack(pady=14)


# ---------------------------------------------------------------------------
# ========== 2) HASTA ANA PENCERESİ =========================================
# ---------------------------------------------------------------------------

def run_patient(info: dict) -> None:
    root = tk.Tk()
    root.title("Hasta Paneli")
    root.state("zoomed")  # Başlık çubuğu kalır, pencere maksimize olur
    style = create_style()

    # Sol menü & sağ içerik alanı
    main = ttk.Frame(root)
    main.pack(fill="both", expand=True)

    left = ttk.Frame(main, padding=20, width=240)
    left.pack(side="left", fill="y")

    right = ttk.Frame(main)
    right.pack(side="right", fill="both", expand=True)

    # Sol panel üstüne profil resmi + ad-soyad
    profile_frame = ttk.Frame(left)
    profile_frame.pack(pady=(0, 20))

    # Profil resmi (varsayılan ya da yüklenmişse)
    result = Database().fetch_one("SELECT profil_resmi_path FROM kullanicilar WHERE id = %s", (info["id"],))
    img_path = result[0] if result else None

    if img_path and os.path.exists(img_path):
        from PIL import Image, ImageTk
        img = Image.open(img_path).resize((80, 80))
        photo = ImageTk.PhotoImage(img)
    else:
        # Boş avatar simgesi
        photo = tk.PhotoImage(width=80, height=80)

    img_label = tk.Label(profile_frame, image=photo)
    img_label.image = photo
    img_label.pack()

    # Ad Soyad
    tk.Label(profile_frame, text=f"{info['ad']} {info['soyad']}", font=("Segoe UI", 10, "bold")).pack(pady=(6, 0))

    # ------------------------------------------------------------------
    # Pop‑up açan eski modülleri gömülü hâle getirme yardımcıları
    # ------------------------------------------------------------------

    def embed_external(callable_fn):
        """callable_fn pop‑up yerine *right* paneli içinde çalışsın."""
        for child in right.winfo_children():
            child.destroy()

        container = ttk.Frame(right)
        container.pack(fill="both", expand=True)

        # Geçici olarak tk.Toplevel'i saptırıyoruz
        orig_toplevel = tk.Toplevel

        class FakeToplevel(tk.Frame):
            def __init__(self, *args, **kwargs):
                super().__init__(container)
                self.pack(fill="both", expand=True)

            def title(self, *a, **kw):
                pass

            def geometry(self, *a, **kw):
                pass

            def state(self, *a, **kw):
                pass

            def update_idletasks(self, *a, **kw):
                pass

            def resizable(self, *a, **kw):
                pass

            def destroy(self):
                super().destroy()


        tk.Toplevel = FakeToplevel  # Patch
        try:
            callable_fn()
        finally:
            tk.Toplevel = orig_toplevel  # Patch'i geri al

    # Sağ panel kullanan fonksiyonlar
    def show_in_right(builder):
        for child in right.winfo_children():
            child.destroy()
        builder()

    # Ana işlemler & komutlar
    buttons = [
        ("Kan Şekeri Ekle", lambda: show_in_right(lambda: add_blood_sugar_ui(info["id"], right))),
        ("Kan Şekeri Verilerini Görüntüle", lambda: embed_external(lambda: show(info["id"]))),
        (
            "Diyet / Egzersiz Önerilerini Uygula",
            lambda: embed_external(lambda: open_pending_recommendations(info["id"])),
        ),
        ("Öneri Uygulama Durumu", lambda: show_in_right(lambda: show_progress(info["id"], right))),
        ("Kan Şekeri Grafiğini Göster", lambda: show_in_right(lambda: show_blood_sugar_graph(info["id"], right))),
        ("Hasta Bilgisi", lambda: embed_external(lambda: open_kisi_bilgisi_window(info["id"]))),
    ]

    # Renk paleti (materyal tasarım tonları)
    palette = [
        "#EF5350",  # kırmızı
        "#FB8C00",  # turuncu
        "#8BC34A",  # yeşil
        "#42A5F5",  # mavi
        "#AB47BC",  # mor
        "#FFB300",  # amber
    ]

    for i, (text, cmd) in enumerate(buttons):
        style_name = f"Color{i}.TButton"
        bg = palette[i % len(palette)]
        if style_name not in style.element_names():
            style.configure(
                style_name,
                font=("Segoe UI", 10, "bold"),
                foreground="white",
                background=bg,
                padding=6,
            )
            style.map(style_name, background=[("active", bg)])
        ttk.Button(left, text=text, command=cmd, style=style_name).pack(fill="x", pady=4)

    ttk.Button(left, text="Çıkış", command=root.destroy).pack(pady=(14, 0))

    root.mainloop()


# ---------------------------------------------------------------------------
# ========== 3) ÖNERİ UYGULAMA YÜZDESİ GRAFİĞİ ==============================
# ---------------------------------------------------------------------------

def show_progress(hasta_id: int, parent: tk.Widget | None = None):
    db = Database();
    db.connect()
    diyet_oran, egzersiz_oran = db.get_recommendation_progress(hasta_id)
    db.close()

    if parent is None:
        win = tk.Toplevel()
        win.title("Öneri Uygulama Yüzdesi")
        center_window(win, 520, 420)
        create_style()
        container = win
    else:
        for child in parent.winfo_children():
            child.destroy()
        container = parent

    fig, ax = plt.subplots(figsize=(5, 3.5))
    kategoriler = ["Diyet", "Egzersiz"]
    oranlar = [diyet_oran, egzersiz_oran]
    colors = ["#4CAF50", "#2196F3"]

    bars = ax.bar(kategoriler, oranlar, color=colors)
    ax.set_ylim(0, 100)
    ax.set_ylabel("Uygulama Oranı (%)")
    ax.set_title("Diyet ve Egzersiz Uygulama Yüzdesi")

    for bar, oran in zip(bars, oranlar):
        height = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width() / 2.0,
            height + 3,
            f"{oran:.0f}%",
            ha="center",
            va="bottom",
            fontsize=10,
        )

    canvas = FigureCanvasTkAgg(fig, master=container)
    canvas.draw()
    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    if isinstance(container, tk.Toplevel):
        ttk.Button(container, text="Kapat", command=container.destroy).pack(pady=6)


# ---------------------------------------------------------------------------
# ========== 4) GÜNLÜK KAN ŞEKERİ GRAFİĞİ ==================================
# ---------------------------------------------------------------------------

def show_blood_sugar_graph(hasta_id: int, parent: tk.Widget | None = None):
    db = Database();
    db.connect()
    data = db.get_insulin_averages_for_graph(hasta_id)
    db.close()

    if not data:
        messagebox.showinfo("Bilgi", "Gösterilecek kan şekeri verisi bulunamadı.")
        return

    tarih_list = [row[0].strftime("%d.%m.%Y") for row in data]
    ortalama_list = [float(row[1]) for row in data]

    if parent is None:
        win = tk.Toplevel()
        win.title("Günlük Kan Şekeri Grafiği")
        center_window(win, 640, 460)
        create_style()
        container = win
    else:
        for child in parent.winfo_children():
            child.destroy()
        container = parent

    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot(tarih_list, ortalama_list, marker="o", linestyle="-", color="blue")
    ax.set_title("Günlük Ortalama Kan Şekeri Seviyesi")
    ax.set_xlabel("Tarih")
    ax.set_ylabel("Ortalama Seviye (mg/dL)")
    ax.tick_params(axis="x", rotation=45)

    canvas = FigureCanvasTkAgg(fig, master=container)
    canvas.draw()
    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    if isinstance(container, tk.Toplevel):
        ttk.Button(container, text="Kapat", command=container.destroy).pack(pady=6)


# ---------------------------------------------------------------------------
# ========== 5) Giriş Ekranına Dönüş ========================================
# ---------------------------------------------------------------------------

def back_to_login(window: tk.Toplevel | tk.Tk):
    window.destroy()
    from main import run_entry  # Döngüde importı kırmamak için lokal import

    run_entry()
