import re
from loguru import logger


def normalize_currency(value: object) -> float:
    """Convert Brazilian currency formats to float. Returns 0.0 on failure."""
    if value is None or value == "":
        return 0.0
    if isinstance(value, (int, float)):
        if value != value:
            logger.warning("normalize_currency: received NaN, returning 0.0")
            return 0.0
        return float(value)
    raw = str(value).strip()
    raw = raw.replace("R$", "").replace("\xa0", "").strip()
    raw = re.sub(r"\.", "", raw)
    raw = raw.replace(",", ".")
    try:
        return float(raw)
    except ValueError:
        logger.warning("normalize_currency: cannot parse '{}', returning 0.0", value)
        return 0.0
