def remove_empty_rows(matrix: list[list]) -> list[list]:
    """Remove rows where every cell is empty string or None."""
    return [row for row in matrix if any(cell not in (None, "", " ") for cell in row)]
