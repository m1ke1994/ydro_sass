import re


ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
PHONE_RE = re.compile(r"^\+?[0-9\s\-()]{7,20}$")


def normalize_phone(value):
    if value is None:
        return None
    phone = str(value).strip()
    if not phone:
        return None
    if ISO_DATE_RE.fullmatch(phone):
        return None
    if not PHONE_RE.fullmatch(phone):
        return None
    digits = re.sub(r"\D", "", phone)
    if len(digits) < 7:
        return None
    return phone
