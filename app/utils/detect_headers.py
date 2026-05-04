from app.core.field_maps import resolve_field
from app.utils.normalize_text import normalize_for_compare

_MONTH_TOKENS = {
    "jan", "fev", "mar", "abr", "mai", "jun",
    "jul", "ago", "set", "out", "nov", "dez",
    "janeiro", "fevereiro", "março", "marco", "abril", "maio",
    "junho", "julho", "agosto", "setembro", "outubro", "novembro", "dezembro",
}


def is_month_label(cell: str) -> bool:
    v = normalize_for_compare(str(cell)).strip()
    # "mai/2026", "2026-05", "maio 2026"
    if any(v.startswith(m) for m in _MONTH_TOKENS):
        return True
    import re
    return bool(re.match(r"\d{4}[-/]\d{2}$", v))


def detect_header_row(matrix: list[list]) -> int:
    """Return index of the first row that looks like a header (highest known-field hit rate)."""
    best_row, best_score = 0, -1
    for i, row in enumerate(matrix):
        hits = sum(1 for cell in row if cell and resolve_field(str(cell)) is not None)
        if hits > best_score:
            best_score, best_row = hits, i
    return best_row


def detect_month_columns(header_row: list) -> list[int]:
    """Return column indices that appear to be month labels."""
    return [i for i, cell in enumerate(header_row) if cell and is_month_label(str(cell))]
