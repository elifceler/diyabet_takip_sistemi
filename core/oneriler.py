def get_recommendations(kan_sekeri, belirtiler):
    """
    Kan şekeri değeri ve belirtilere göre diyet ve egzersiz önerisi üretir.
    :param kan_sekeri: int veya float (mg/dL cinsinden)
    :param belirtiler: list[str]
    :return: (diyet, egzersiz)
    """

    kan_sekeri = float(kan_sekeri)
    belirtiler = [b.strip().lower() for b in belirtiler]

    # Kurallar aşağıdan yukarıya doğru kontrol edilir
    if kan_sekeri < 70:
        if any(b in belirtiler for b in ["nöropati", "polifaji", "yorgunluk"]):
            return "Dengeli Beslenme", "Yok"
    elif 70 <= kan_sekeri <= 110:
        if any(b in belirtiler for b in ["yorgunluk", "kilo kaybı"]):
            return "Az Şekerli Diyet", "Yürüyüş"
        if any(b in belirtiler for b in ["polifaji", "polidipsi"]):
            return "Dengeli Beslenme", "Yürüyüş"
    elif 110 < kan_sekeri < 180:
        if any(b in belirtiler for b in ["bulanık görme", "nöropati"]):
            return "Az Şekerli Diyet", "Klinik Egzersiz"
        if any(b in belirtiler for b in ["poliüri", "polidipsi"]):
            return "Şekersiz Diyet", "Klinik Egzersiz"
        if any(b in belirtiler for b in ["yorgunluk", "nöropati", "bulanık görme"]):
            return "Az Şekerli Diyet", "Yürüyüş"
    elif kan_sekeri >= 180:
        if any(b in belirtiler for b in ["yaraların yavaş iyileşmesi", "polifaji", "polidipsi"]):
            return "Şekersiz Diyet", "Klinik Egzersiz"
        if any(b in belirtiler for b in ["yaraların yavaş iyileşmesi", "kilo kaybı"]):
            return "Şekersiz Diyet", "Yürüyüş"

    return "Genel Diyet", "Egzersiz Planı"


# Örnek kullanım
if __name__ == "__main__":
    diyet, egzersiz = get_recommendations(145, ["Yorgunluk", "Nöropati"])
    print("Diyet:", diyet)
    print("Egzersiz:", egzersiz)
