import re
import unicodedata


def normalize_text(value: str) -> str:
    """Strip invisible chars, collapse whitespace, trim."""
    if not isinstance(value, str):
        value = str(value)
    value = re.sub(r"[​‌‍﻿­]", "", value)
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def normalize_for_compare(value: str) -> str:
    """Lowercase + remove accents for internal comparison only. Output not for display."""
    value = normalize_text(value)
    nfd = unicodedata.normalize("NFD", value)
    return "".join(c for c in nfd if unicodedata.category(c) != "Mn").lower()
