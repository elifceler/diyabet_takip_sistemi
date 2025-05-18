import tkinter as tk
from core.database import Database
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import matplotlib.lines as mlines

def show_combined_graph(hasta_id: int):
    db = Database(); db.connect()
    rows = db.get_diet_exercise_blood_sugar_graph_data(hasta_id)
    db.close()

    if not rows:
        from tkinter import messagebox
        messagebox.showinfo("Bilgi", "Gösterilecek grafik verisi bulunamadı.")
        return

    tarihler = []
    seviyeler = []
    renkler = []
    markerlar = []

    renk_haritasi = {}
    renkler_listesi = ["blue", "green", "orange", "purple", "red", "brown"]
    marker_map = {True: "o", False: "X"}

    for row in rows:
        tarih, diyet, diyet_durumu, egzersiz_durumu, ort = row
        if ort is None:
            continue
        t_str = tarih.strftime("%d.%m")
        if diyet not in renk_haritasi:
            renk_haritasi[diyet] = renkler_listesi[len(renk_haritasi) % len(renkler_listesi)]

        tarihler.append(t_str)
        seviyeler.append(ort)
        renkler.append(renk_haritasi[diyet])
        markerlar.append(marker_map[egzersiz_durumu])



    fig, ax = plt.subplots(figsize=(12, 6))  # Daha geniş görünüm
    for i in range(len(tarihler)):
        ax.scatter(tarihler[i], seviyeler[i], color=renkler[i], marker=markerlar[i], s=100)

    # Noktaları çizgiyle birleştir — aynı sırada olmalı
    ax.plot(tarihler, seviyeler, color="gray", linestyle='-', linewidth=1, alpha=0.5)

    ax.set_title("Diyet/Egzersiz – Kan Şekeri İlişkisi")
    ax.set_xlabel("Tarih")
    ax.set_ylabel("Ortalama Kan Şekeri (mg/dL)")
    ax.grid(True)
    ax.tick_params(axis='x', rotation=45)

    # Özel legend: diyetler (renk), egzersiz (şekil) ayrı ayrı gösterilecek
    legend_elements = []

    # Diyet türlerine göre renkli daireler
    for diyet, renk in renk_haritasi.items():
        legend_elements.append(
            mlines.Line2D([], [], color=renk, marker='o', linestyle='None',
                          markersize=10, label=diyet)
        )

    # Egzersiz durumu için siyah şekiller
    legend_elements.append(
        mlines.Line2D([], [], color='black', marker='o', linestyle='None',
                      markersize=10, label='Egzersiz Yapıldı')
    )
    legend_elements.append(
        mlines.Line2D([], [], color='black', marker='X', linestyle='None',
                      markersize=10, label='Egzersiz Yapılmadı')
    )

    ax.legend(handles=legend_elements, loc="best")

    # Grafik pencereyi göster
    win = tk.Toplevel()
    win.title("İlişkisel Grafik")
    canvas = FigureCanvasTkAgg(fig, master=win)
    canvas.draw()
    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
