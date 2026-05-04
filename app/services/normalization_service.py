from app.core.field_maps import resolve_field
from app.services.sheet_parser_service import ParsedBlock
from app.utils.normalize_currency import normalize_currency
from app.utils.normalize_date import normalize_date
from app.utils.normalize_number import normalize_number
from app.utils.normalize_text import normalize_text, normalize_for_compare

_CURRENCY_FIELDS = {"bruto", "liquido", "valor", "comissao_sdr", "comissao_closer", "meta_mensal"}
_DATE_FIELDS = {"data"}
_NUMBER_FIELDS = {
    "conexoes_enviadas", "conexoes_aceitas", "abordagens", "inmails_enviados",
    "followups", "numeros_captados", "ligacoes_agendadas", "reunioes_agendadas",
    "reunioes_realizadas", "ligacoes_realizadas", "indicacoes", "indicacoes_captadas",
    "meta_numeros", "meta_leads", "meta_ligacoes", "meta_reunioes", "meta_indicacoes",
}


def _normalize_cell(canonical: str | None, raw_value: object) -> object:
    if raw_value is None or raw_value == "":
        return "" if canonical not in (_CURRENCY_FIELDS | _DATE_FIELDS | _NUMBER_FIELDS) else 0
    if canonical in _CURRENCY_FIELDS:
        return normalize_currency(raw_value)
    if canonical in _DATE_FIELDS:
        dt = normalize_date(raw_value)
        return dt.isoformat() if dt else None
    if canonical in _NUMBER_FIELDS:
        return normalize_number(raw_value, field_hint=canonical or "")
    return normalize_text(str(raw_value))


def normalize_matrix(blocks: list[ParsedBlock]) -> list[dict]:
    """Convert ParsedBlock list into flat list of normalized dicts for debug output."""
    result = []
    for block_idx, block in enumerate(blocks):
        for row in block.rows:
            normalized_row: dict = {"_block": block_idx}
            for header, cell in row.items():
                canonical = resolve_field(header)
                normalized_row[header] = _normalize_cell(canonical, cell.value)
                if canonical and canonical != header:
                    normalized_row[f"_{canonical}"] = normalized_row[header]
            result.append(normalized_row)
    return result
