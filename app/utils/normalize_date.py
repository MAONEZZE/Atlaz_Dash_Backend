import re
from datetime import datetime, timezone
from typing import Optional

from dateutil import parser as dateutil_parser

_MONTH_PT = {
    "jan": 1, "fev": 2, "mar": 3, "abr": 4, "mai": 5, "jun": 6,
    "jul": 7, "ago": 8, "set": 9, "out": 10, "nov": 11, "dez": 12,
    "janeiro": 1, "fevereiro": 2, "março": 3, "marco": 3, "abril": 4,
    "maio": 5, "junho": 6, "julho": 7, "agosto": 8, "setembro": 9,
    "outubro": 10, "novembro": 11, "dezembro": 12,
}


def _try_pt_month_year(value: str) -> Optional[datetime]:
    """Parse 'mai/2026' or 'maio 2026' into first day of that month."""
    v = value.strip().lower()
    m = re.match(r"([a-zçã]+)[/ ](\d{4})", v)
    if not m:
        return None
    month_key = m.group(1)
    year = int(m.group(2))
    month = _MONTH_PT.get(month_key)
    if not month:
        return None
    return datetime(year, month, 1, tzinfo=timezone.utc)


def normalize_date(value: object) -> Optional[datetime]:
    """Accept ms timestamp, dd/mm/yyyy, yyyy-mm-dd, mai/2026, maio 2026."""
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        try:
            return datetime.fromtimestamp(float(value) / 1000, tz=timezone.utc)
        except (OSError, OverflowError, ValueError):
            return None
    raw = str(value).strip()
    pt = _try_pt_month_year(raw)
    if pt:
        return pt
    if re.match(r"\d{2}/\d{2}/\d{4}", raw):
        try:
            return datetime.strptime(raw, "%d/%m/%Y").replace(tzinfo=timezone.utc)
        except ValueError:
            pass
    try:
        return dateutil_parser.parse(raw).replace(tzinfo=timezone.utc)
    except (ValueError, OverflowError):
        return None
