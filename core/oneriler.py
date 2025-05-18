# core/oneriler.py
# ────────────────────────────────────────────────────────────────────────────────
"""
Diyabet Takip Sistemi – Diyet & Egzersiz Öneri Motoru

• Kan şekeri aralığı ve hastanın seçtiği belirtiler kombinasyonuna göre
  uygun diyet ve egzersiz önerisini döndürür.
• Kurallar PDF dokümanındaki tabloya bire bir uyacak şekilde tanımlanmıştır.
"""
from __future__ import annotations

from typing import Optional, Tuple, List, Set


# ──────────────── KURAL TABLOSU ────────────────
# Her kural beş öğeden oluşur:
#   (alt_sınır, üst_sınır, belirtiler_seti, diyet, egzersiz)
# • alt_sınır / üst_sınır None ise: açık uçlu (örn. < 70 mg/dL veya ≥ 180 mg/dL)
# • Belirtiler tam eşleşmeli (seçimler == kural) olacak şekilde kontrol ediliyor.
_RULES: List[Tuple[Optional[float], Optional[float], Set[str], str, str]] = [
    # < 70 mg/dL  – Hipoglisemi
    (
        None,
        70,
        {"nöropati", "polifaji", "yorgunluk"},
        "Dengeli Beslenme",
        "Yok",
    ),
    # 70 – 110 mg/dL – Normal (alt düzey)
    (
        70,
        110,
        {"yorgunluk", "kilo kaybı"},
        "Az Şekerli Diyet",
        "Yürüyüş",
    ),
    (
        70,
        110,
        {"polifaji", "polidipsi"},
        "Dengeli Beslenme",
        "Yürüyüş",
    ),
    # 110 – 180 mg/dL – Normal (üst düzey) / Hafif yüksek
    (
        110,
        180,
        {"bulanık görme", "nöropati"},
        "Az Şekerli Diyet",
        "Klinik Egzersiz",
    ),
    (
        110,
        180,
        {"poliüri", "polidipsi"},
        "Şekersiz Diyet",
        "Klinik Egzersiz",
    ),
    (
        110,
        180,
        {"yorgunluk", "nöropati", "bulanık görme"},
        "Az Şekerli Diyet",
        "Yürüyüş",
    ),
    # ≥ 180 mg/dL – Hiperglisemi
    (
        180,
        None,
        {"yaraların yavaş iyileşmesi", "polifaji", "polidipsi"},
        "Şekersiz Diyet",
        "Klinik Egzersiz",
    ),
    (
        180,
        None,
        {"yaraların yavaş iyileşmesi", "kilo kaybı"},
        "Şekersiz Diyet",
        "Yürüyüş",
    ),
]


# ────────────────────────────────────────────────────────────────────────────────
def _normalize(text: str) -> str:
    """
    Küçük-harf + baştaki/sondaki boşlukları kırp + Türkçe karakter duyarlı normalize.
    Python'un .lower() metodu Unicode-uyumlu olduğu için ek işleme gerek yok.
    """
    return text.strip().lower()


def get_recommendations(
    ks_value: float,
    symptoms: List[str],
) -> Optional[Tuple[str, str]]:
    """
    Parametreler
    ------------
    ks_value : float
        Hastanın ölçtüğü kan şekeri (mg/dL).
    symptoms : List[str]
        Kullanıcının GUI’den seçtiği belirtiler.

    Döndürür
    --------
    (diyet, egzersiz)  → Eşleşme bulunduysa
    None               → Hiçbir kural tam olarak uyuşmadı
    """
    # Kullanıcının seçtiği belirtileri normalize et
    selected: Set[str] = {_normalize(b) for b in symptoms}

    # Her kuralı sırayla kontrol et
    for low, high, rule_set, diet, exercise in _RULES:
        # Kan şekeri aralığı
        if low is not None and ks_value < low:
            continue
        if high is not None and ks_value > high:
            continue

        # Belirti kümesi tam eşleşmeli (ne eksik ne fazla)
        if selected == rule_set:
            return diet, exercise

    # Uyumlu kural yok
    return None


# —————————————————— Modül testleri ——————————————————
if __name__ == "__main__":
    # 1) Pozitif test – Şekersiz Diyet, Klinik Egzersiz
    print(get_recommendations(152, ["Poliüri", "Polidipsi"]))
    # 2) Negatif test – Kurala bire bir uymadığı için None
    print(get_recommendations(152, ["Poliüri", "Polidipsi", "Kilo Kaybı"]))