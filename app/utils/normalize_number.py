import math
from loguru import logger


def normalize_number(value: object, field_hint: str = "") -> int | float:
    """Convert any value to a number. Returns 0 on empty/invalid. Never NaN/None."""
    if value is None or value == "":
        return 0
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, (int, float)):
        if math.isnan(value) or math.isinf(value):
            logger.warning("normalize_number: NaN/Inf for field='{}', returning 0", field_hint)
            return 0
        return value
    raw = str(value).strip().replace(",", ".").replace("\xa0", "")
    if raw == "" or raw == "-":
        return 0
    try:
        f = float(raw)
        return 0 if (math.isnan(f) or math.isinf(f)) else f
    except ValueError:
        logger.warning("normalize_number: cannot parse '{}' for field='{}', returning 0", value, field_hint)
        return 0
