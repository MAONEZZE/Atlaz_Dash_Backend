import re
from loguru import logger


def normalize_percentage(value: object, as_fraction: bool = False) -> float:
    """
    Parse percentage to float.
    as_fraction=False → returns 10.0 for "10%"
    as_fraction=True  → returns 0.10 for "10%"
    """
    if value is None or value == "":
        return 0.0
    if isinstance(value, (int, float)):
        v = float(value)
        return v / 100 if as_fraction and v > 1 else v
    raw = str(value).strip()
    has_pct = "%" in raw
    raw = raw.replace("%", "").replace(",", ".").strip()
    try:
        v = float(raw)
    except ValueError:
        logger.warning("normalize_percentage: cannot parse '{}', returning 0.0", value)
        return 0.0
    if has_pct and as_fraction:
        return v / 100
    return v
