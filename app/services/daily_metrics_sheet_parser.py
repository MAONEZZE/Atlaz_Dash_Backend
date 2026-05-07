"""
Parser for the "Métricas Diárias" tab in per-seller Google Sheets.

Sheet layout:
  Row 0: headers  (column names)
  Row 1: "Meta"   (daily targets — first cell is the label "Meta")
  Rows 2+: one row per day (date/day-number in first column, values in other columns)

Returns DailyMetricsSheet with meta_row (daily targets) and daily_rows (per-day values).
Tolerant: skips unrecognized columns, defaults missing/invalid values to 0.
"""

from dataclasses import dataclass, field

from app.utils.normalize_number import normalize_number
from app.utils.normalize_text import normalize_for_compare

# ---------------------------------------------------------------------------
# Column-name → canonical field mapping
# Covers all expected SDR and Closer metric columns.
# Keys are the normalized (no-accent, lowercase) forms of the column header.
# ---------------------------------------------------------------------------
_SDR_FIELDS: dict[str, str] = {
    normalize_for_compare("Conexões Enviadas"): "conexoes_enviadas",
    normalize_for_compare("Conexoes Enviadas"): "conexoes_enviadas",
    normalize_for_compare("Conexões Aceitas"): "conexoes_aceitas",
    normalize_for_compare("Conexoes Aceitas"): "conexoes_aceitas",
    normalize_for_compare("Abordagens"): "abordagens",
    normalize_for_compare("InMails Enviados"): "inmails_enviados",
    normalize_for_compare("Inmails Enviados"): "inmails_enviados",
    normalize_for_compare("InMails"): "inmails_enviados",
    normalize_for_compare("Inmails"): "inmails_enviados",
    normalize_for_compare("Follow-ups"): "follow_ups",
    normalize_for_compare("Follow ups"): "follow_ups",
    normalize_for_compare("Followups"): "follow_ups",
    normalize_for_compare("Números Captados"): "numeros_captados",
    normalize_for_compare("Numeros Captados"): "numeros_captados",
    normalize_for_compare("Ligações Agendadas"): "ligacoes_agendadas",
    normalize_for_compare("Ligacoes Agendadas"): "ligacoes_agendadas",
    normalize_for_compare("Indicações Captadas"): "indicacoes_captadas",
    normalize_for_compare("Indicacoes Captadas"): "indicacoes_captadas",
}

_CLOSER_FIELDS: dict[str, str] = {
    normalize_for_compare("Ligações Realizadas"): "ligacoes_realizadas",
    normalize_for_compare("Ligacoes Realizadas"): "ligacoes_realizadas",
    normalize_for_compare("Reuniões Agendadas"): "reunioes_agendadas",
    normalize_for_compare("Reunioes Agendadas"): "reunioes_agendadas",
    normalize_for_compare("Reuniões Realizadas"): "reunioes_realizadas",
    normalize_for_compare("Reunioes Realizadas"): "reunioes_realizadas",
    normalize_for_compare("Indicações"): "indicacoes",
    normalize_for_compare("Indicacoes"): "indicacoes",
}

_ALL_FIELDS: dict[str, str] = {**_SDR_FIELDS, **_CLOSER_FIELDS}


def _resolve_column(header: str) -> str | None:
    """Return canonical field name for a header string, or None if unrecognized."""
    return _ALL_FIELDS.get(normalize_for_compare(header))


def _is_meta_label(cell: str) -> bool:
    """Return True if the first-column cell marks a "Meta" (goal) row."""
    normalized = normalize_for_compare(str(cell).strip())
    return normalized == "meta" or normalized.startswith("meta ")


def _is_empty_row(row: list) -> bool:
    return not any(str(c).strip() for c in row)


@dataclass
class DailyRow:
    date: str                        # raw date string from sheet, e.g. "01/05", "1", "2025-05-01"
    values: dict[str, int] = field(default_factory=dict)  # canonical field → value


@dataclass
class DailyMetricsSheet:
    meta_row: dict[str, int]         # daily targets (from "Meta" row)
    daily_rows: list[DailyRow]       # one per calendar day present in the sheet


def parse_daily_metrics(matrix: list[list], role: str) -> DailyMetricsSheet:
    """
    Parse a "Métricas Diárias" raw matrix returned by read_tab().

    role: "closer" or "sdr" — controls which metric fields are extracted;
          unrecognized columns are always skipped regardless.

    Returns DailyMetricsSheet with:
      - meta_row: dict of canonical_field → int (daily target values)
      - daily_rows: list[DailyRow] (one per day row found in the sheet)
    """
    if not matrix:
        return DailyMetricsSheet(meta_row={}, daily_rows=[])

    # --- Row 0: headers ---
    header_row: list = matrix[0] if matrix else []

    # Build column-index → canonical-field mapping (skip first column = date/label column)
    col_map: dict[int, str] = {}
    for col_idx, header in enumerate(header_row):
        if col_idx == 0:
            continue  # first column is always the date/label column
        canonical = _resolve_column(str(header).strip())
        if canonical is not None:
            col_map[col_idx] = canonical

    def _extract_values(row: list) -> dict[str, int]:
        """Extract canonical field values from a data row."""
        result: dict[str, int] = {}
        for col_idx, canonical in col_map.items():
            raw = row[col_idx] if col_idx < len(row) else ""
            result[canonical] = int(normalize_number(raw, field_hint=canonical))
        return result

    meta_row: dict[str, int] = {}
    daily_rows: list[DailyRow] = []

    for row_idx, row in enumerate(matrix):
        if row_idx == 0:
            # Skip the header row
            continue

        if _is_empty_row(row):
            continue

        first_cell = str(row[0]).strip() if row else ""

        if _is_meta_label(first_cell):
            # This is the Meta (goal) row
            meta_row = _extract_values(row)
            continue

        # Otherwise treat as a daily data row
        daily_rows.append(DailyRow(
            date=first_cell,
            values=_extract_values(row),
        ))

    return DailyMetricsSheet(meta_row=meta_row, daily_rows=daily_rows)
