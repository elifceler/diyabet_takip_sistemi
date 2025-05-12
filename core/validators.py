# core/validators.py
import re
from datetime import datetime

TC_REGEX     = re.compile(r"^\d{11}$")
EMAIL_REGEX  = re.compile(r"^[\w\.-]+@[\w\.-]+\.\w{2,}$")
DATE_DISPLAY = "%d.%m.%Y"      # GG.AA.YYYY
DATE_SQL     = "%Y-%m-%d"      # ISO

def validate_tc(tc: str) -> bool:
    return bool(TC_REGEX.match(tc))

def validate_email(mail: str) -> bool:
    return bool(EMAIL_REGEX.match(mail))

def validate_date(date_str: str) -> str | None:
    """
    GG.AA.YYYY biçimindeki string’i doğrular.
    Geçerliyse YYYY-MM-DD biçiminde döndürür.
    """
    try:
        d = datetime.strptime(date_str, DATE_DISPLAY).date()
        return d.strftime(DATE_SQL)
    except ValueError:
        return None
