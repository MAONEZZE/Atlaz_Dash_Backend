def remove_empty_columns(matrix: list[list]) -> list[list]:
    """Remove columns where every row cell is empty. Pads short rows first."""
    if not matrix:
        return matrix
    max_cols = max(len(row) for row in matrix)
    padded = [row + [""] * (max_cols - len(row)) for row in matrix]
    non_empty_cols = [
        c for c in range(max_cols)
        if any(padded[r][c] not in (None, "", " ") for r in range(len(padded)))
    ]
    return [[row[c] for c in non_empty_cols] for row in padded]
