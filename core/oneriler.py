# core/oneriler.py
# ────────────────────────────────────────────────────────────────────────────────
"""
Diyabet Takip Sistemi – Diyet & Egzersiz Öneri Motoru
"""
from __future__ import annotations

import re, unicodedata
from typing import Optional, Tuple, List, Set

# ───────────────────────── Yardımcı ─────────────────────────
def _normalize(txt: str) -> str:
    """
    • Unicode ayrıştır → NFKD
    • Aksan işaretlerini (Mn) at
    • Küçük harf + çoklu boşluk → tek boşluk
    """
    txt = unicodedata.normalize("NFKD", txt)
    txt = "".join(ch for ch in txt if unicodedata.category(ch) != "Mn")
    txt = txt.lower()
    txt = re.sub(r"\s+", " ", txt).strip()
    return txt

# ───────────────────────── KURALLAR ─────────────────────────
_RAW_RULES: List[Tuple[Optional[float], Optional[float], Set[str], str, str]] = [
    (None, 70, {"Nöropati", "Polifaji", "Yorgunluk"},                      "Dengeli Beslenme", "Yok"),
    (70, 110, {"Yorgunluk", "Kilo Kaybı"},                                "Az Şekerli Diyet", "Yürüyüş"),
    (70, 110, {"Polifaji", "Polidipsi"},                                  "Dengeli Beslenme", "Yürüyüş"),
    (110, 180, {"Bulanık Görme", "Nöropati"},                             "Az Şekerli Diyet", "Klinik Egzersiz"),
    (110, 180, {"Poliüri", "Polidipsi"},                                  "Şekersiz Diyet",   "Klinik Egzersiz"),
    (110, 180, {"Yorgunluk", "Nöropati", "Bulanık Görme"},                "Az Şekerli Diyet", "Yürüyüş"),
    (180, None, {"Yaraların Yavaş İyileşmesi", "Polifaji", "Polidipsi"},   "Şekersiz Diyet",   "Klinik Egzersiz"),
    (180, None, {"Yaraların Yavaş İyileşmesi", "Kilo Kaybı"},              "Şekersiz Diyet",   "Yürüyüş"),  # Özel kural
]

# Kuralları ön-normalize et – tek seferlik
_RULES = [
    (lo, hi, {_normalize(b) for b in s}, diet, ex)
    for lo, hi, s, diet, ex in _RAW_RULES
]

# ───────────────────────── Ana Fonksiyon ─────────────────────────
def get_recommendations(ks: float, symptoms: List[str]) -> Optional[Tuple[str, str]]:
    selected = {_normalize(sym) for sym in symptoms}

    for lo, hi, rule_set, diet, ex in _RULES:
        if lo is not None and ks < lo:  continue
        if hi is not None and ks > hi:  continue
        if selected == rule_set:        return diet, ex
    return None

# ───────────────────────── Hızlı Test ─────────────────────────
if __name__ == "__main__":
    print(get_recommendations(190, ["Kilo  Kaybı", "Yaraların   Yavaş İyileşmesi"]))
    # ('Şekersiz Diyet', 'Yürüyüş')
