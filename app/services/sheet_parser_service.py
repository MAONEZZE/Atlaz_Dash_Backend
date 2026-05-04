from dataclasses import dataclass, field
from typing import Any

from app.utils.detect_headers import detect_header_row, detect_month_columns, is_month_label
from app.utils.normalize_text import normalize_for_compare
from app.utils.remove_empty_columns import remove_empty_columns
from app.utils.remove_empty_rows import remove_empty_rows


@dataclass
class ParsedCell:
    value: Any
    orig_row: int
    orig_col: int


@dataclass
class ParsedBlock:
    header_row_idx: int
    headers: list[str]
    rows: list[dict[str, ParsedCell]]
    month_col_indices: list[int] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def _is_block_title(row: list, known_headers: set[str]) -> bool:
    """Single non-empty cell that does not look like a data value = likely a mid-sheet title."""
    filled = [c for c in row if c not in (None, "", " ")]
    if len(filled) != 1:
        return False
    label = normalize_for_compare(str(filled[0]))
    return label not in known_headers


def parse_tab(matrix: list[list]) -> list[ParsedBlock]:
    """
    Parse a raw sheet matrix into one or more ParsedBlock objects.
    Handles: empty rows/cols, headers not at row 0, mid-sheet block titles,
    month columns, and preserves original (row, col) coordinates.
    """
    if not matrix:
        return []

    cleaned = remove_empty_rows(matrix)
    cleaned = remove_empty_columns(cleaned)

    if not cleaned:
        return []

    header_idx = detect_header_row(cleaned)
    headers = [str(c) for c in cleaned[header_idx]]
    month_cols = detect_month_columns(headers)

    known_header_set = {normalize_for_compare(h) for h in headers if h}

    blocks: list[ParsedBlock] = []
    current_block = ParsedBlock(
        header_row_idx=header_idx,
        headers=headers,
        rows=[],
        month_col_indices=month_cols,
    )

    for row_idx, row in enumerate(cleaned):
        if row_idx <= header_idx:
            continue

        padded = row + [""] * (len(headers) - len(row))

        if _is_block_title(padded, known_header_set):
            if current_block.rows:
                blocks.append(current_block)
            new_headers = [str(c) for c in padded if c not in (None, "", " ")]
            current_block = ParsedBlock(
                header_row_idx=row_idx,
                headers=new_headers if len(new_headers) > 1 else headers,
                rows=[],
                month_col_indices=month_cols,
            )
            continue

        row_dict: dict[str, ParsedCell] = {}
        for col_idx, cell_val in enumerate(padded):
            if col_idx >= len(current_block.headers):
                break
            col_name = current_block.headers[col_idx]
            row_dict[col_name] = ParsedCell(
                value=cell_val,
                orig_row=row_idx,
                orig_col=col_idx,
            )
        if any(pc.value not in (None, "", " ") for pc in row_dict.values()):
            current_block.rows.append(row_dict)

    if current_block.rows:
        blocks.append(current_block)

    if not blocks and cleaned:
        # Fallback: return header + all rows as single block with no data rows
        blocks.append(ParsedBlock(
            header_row_idx=header_idx,
            headers=headers,
            rows=[],
            month_col_indices=month_cols,
            warnings=["No data rows found after header"],
        ))

    return blocks


def pivot_month_columns(block: ParsedBlock, row_key_fields: list[str]) -> list[dict]:
    """
    Pivot horizontal month columns into vertical rows.
    row_key_fields: headers to carry forward per output row (e.g. ["nome", "cargo"]).
    Returns list of flat dicts with 'mes' + value added.
    """
    result: list[dict] = []
    for row in block.rows:
        base = {f: row[f].value for f in row_key_fields if f in row}
        for col_idx in block.month_col_indices:
            if col_idx >= len(block.headers):
                continue
            month_label = block.headers[col_idx]
            cell = list(row.values())[col_idx] if col_idx < len(row) else None
            entry = dict(base)
            entry["mes"] = month_label
            entry["valor"] = cell.value if cell else ""
            result.append(entry)
    return result


def extract_schema_info(matrix: list[list]) -> dict:
    """Return debug schema: headers, empty rows/cols, financial candidates, date candidates, month cols, warnings."""
    from app.core.field_maps import resolve_field
    from app.utils.detect_headers import is_month_label

    warnings: list[str] = []
    if not matrix:
        return {"warnings": ["Empty matrix"]}

    total_rows = len(matrix)
    max_cols = max((len(r) for r in matrix), default=0)

    empty_row_indices = [i for i, r in enumerate(matrix) if all(c in (None, "", " ") for c in r)]
    empty_col_indices = [
        c for c in range(max_cols)
        if all((matrix[r][c] if c < len(matrix[r]) else "") in (None, "", " ") for r in range(len(matrix)))
    ]

    header_idx = detect_header_row(matrix)
    headers = [str(c) for c in matrix[header_idx]] if header_idx < len(matrix) else []

    financial_candidates = [h for h in headers if resolve_field(h) in (
        "bruto", "liquido", "valor", "comissao_sdr", "comissao_closer", "meta_mensal"
    )]
    date_candidates = [h for h in headers if resolve_field(h) == "data"]
    month_col_headers = [h for h in headers if is_month_label(h)]

    if empty_row_indices:
        warnings.append(f"{len(empty_row_indices)} empty rows detected")
    if empty_col_indices:
        warnings.append(f"{len(empty_col_indices)} empty columns detected")
    if header_idx > 0:
        warnings.append(f"Header detected at row {header_idx}, not row 0")

    return {
        "total_rows": total_rows,
        "total_cols": max_cols,
        "header_row_index": header_idx,
        "detected_headers": headers,
        "empty_row_indices": empty_row_indices,
        "empty_col_indices": empty_col_indices,
        "financial_candidates": financial_candidates,
        "date_candidates": date_candidates,
        "month_column_headers": month_col_headers,
        "warnings": warnings,
    }
