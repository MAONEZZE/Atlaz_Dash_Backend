from app.utils.normalize_text import normalize_for_compare

BASE_VENDAS_SKIP_COLUMNS: set[str] = {
    "Observações",
    "Taxa Cart Jan\n(R$)",
    "Taxa Cart Fev\n(R$)",
    "Taxa Cart Mar\n(R$)",
    "Taxa Cart Abr\n(R$)",
    "Taxa Cart Mai\n(R$)",
    "Taxa Cart Jun\n(R$)",
    "Taxa Cart Jul\n(R$)",
    "Taxa Cart Ago\n(R$)",
    "Taxa Cart Set\n(R$)",
    "Taxa Cart Out\n(R$)",
    "Taxa Cart Nov\n(R$)",
    "Taxa Cart Dez\n(R$)",
}


def filter_columns_by_name(matrix: list[list], skip_names: set[str]) -> list[list]:
    """
    Remove columns whose header matches any name in skip_names.
    Scans all rows to find the one that contains the most skip_names hits,
    then drops those column indices from every row.
    """
    if not matrix or not skip_names:
        return matrix

    normalized_skip = {normalize_for_compare(s) for s in skip_names}
    max_cols = max(len(row) for row in matrix)
    padded = [row + [""] * (max_cols - len(row)) for row in matrix]

    # Find which column indices to drop (any row can be the header row)
    drop_cols: set[int] = set()
    for row in padded:
        for col_idx, cell in enumerate(row):
            if normalize_for_compare(str(cell)) in normalized_skip:
                drop_cols.add(col_idx)

    if not drop_cols:
        return matrix

    keep_cols = [c for c in range(max_cols) if c not in drop_cols]
    return [[row[c] for c in keep_cols] for row in padded]
