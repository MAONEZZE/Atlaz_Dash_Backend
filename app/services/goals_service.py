from loguru import logger

from app.core.field_maps import resolve_field, resolve_name
from app.dtos.goals_dto import SalesGoalsDTO
from app.services.sheet_parser_service import parse_tab
from app.utils.normalize_currency import normalize_currency
from app.utils.normalize_number import normalize_number
from app.utils.normalize_text import normalize_for_compare


def _normalize_cargo(raw: str) -> str:
    v = normalize_for_compare(raw)
    if "sdr" in v or "pre" in v:
        return "SDR"
    if "closer" in v or "vendedor" in v:
        return "Closer"
    return raw.strip().title()


def parse_goals(matrix: list[list]) -> list[SalesGoalsDTO]:
    """Parse METAS tab matrix into SalesGoalsDTO list."""
    if not matrix:
        return []

    blocks = parse_tab(matrix)
    results: list[SalesGoalsDTO] = []

    for block in blocks:
        for row in block.rows:
            # Map parsed cells to canonical fields
            mapped: dict[str, str] = {}
            for header, cell in row.items():
                canonical = resolve_field(header)
                if canonical:
                    mapped[canonical] = str(cell.value) if cell.value not in (None, "") else ""

            nome_raw = mapped.get("nome", "")
            if not nome_raw.strip():
                continue

            nome = resolve_name(nome_raw)
            cargo_raw = mapped.get("cargo", "")
            cargo = _normalize_cargo(cargo_raw) if cargo_raw else ""

            # Skip summary rows and unknown roles (e.g. "Time", header repetitions)
            if cargo not in ("Closer", "SDR"):
                continue

            results.append(SalesGoalsDTO(
                Nome=nome,
                Cargo=cargo,
                Meta_Mensal=normalize_currency(mapped.get("meta_mensal", "")),
                Meta_Numeros=int(normalize_number(mapped.get("meta_numeros", 0))),
                Meta_Leads=int(normalize_number(mapped.get("meta_leads", 0))),
                Meta_Ligacoes=int(normalize_number(mapped.get("meta_ligacoes", 0))),
                Meta_Reunioes=int(normalize_number(mapped.get("meta_reunioes", 0))),
                Meta_Indicacoes=int(normalize_number(mapped.get("meta_indicacoes", 0))),
            ))

    return results
