import pytest
from app.services.sheet_parser_service import parse_tab, pivot_month_columns
from app.utils.remove_empty_rows import remove_empty_rows
from app.utils.remove_empty_columns import remove_empty_columns


def test_remove_empty_rows():
    matrix = [["", ""], ["a", "b"], ["", None], ["c", "d"]]
    result = remove_empty_rows(matrix)
    assert len(result) == 2
    assert result[0] == ["a", "b"]


def test_remove_empty_columns():
    matrix = [["", "a", ""], ["", "b", ""], ["", "c", ""]]
    result = remove_empty_columns(matrix)
    assert all(len(row) == 1 for row in result)
    assert result[0][0] == "a"


def test_parse_tab_simple():
    matrix = [
        ["nome", "cargo", "valor"],
        ["Jacob", "Closer", "1000"],
        ["Jennifer", "SDR", "500"],
    ]
    blocks = parse_tab(matrix)
    assert len(blocks) == 1
    assert len(blocks[0].rows) == 2
    assert blocks[0].rows[0]["nome"].value == "Jacob"


def test_parse_tab_header_at_row_3():
    # Empty rows are stripped before header detection, so header_row_idx is 0 in cleaned matrix
    matrix = [
        ["", "", ""],
        ["", "", ""],
        ["", "", ""],
        ["nome", "cargo", "valor"],
        ["Alex", "Closer", "2000"],
    ]
    blocks = parse_tab(matrix)
    assert len(blocks) >= 1
    # After stripping 3 empty rows, header is at cleaned index 0
    assert blocks[0].header_row_idx == 0
    assert blocks[0].headers == ["nome", "cargo", "valor"]
    assert any(r["nome"].value == "Alex" for r in blocks[0].rows)


def test_parse_tab_empty():
    assert parse_tab([]) == []


def test_parse_tab_month_columns():
    matrix = [
        ["nome", "Jan", "Fev", "Mar"],
        ["Jacob", "1000", "1500", "2000"],
    ]
    blocks = parse_tab(matrix)
    assert len(blocks[0].month_col_indices) == 3


def test_pivot_month_columns():
    matrix = [
        ["nome", "Jan", "Fev"],
        ["Jacob", "1000", "1500"],
    ]
    blocks = parse_tab(matrix)
    pivoted = pivot_month_columns(blocks[0], row_key_fields=["nome"])
    assert len(pivoted) == 2
    assert pivoted[0]["mes"] == "Jan"
    assert pivoted[0]["nome"] == "Jacob"
    assert pivoted[1]["mes"] == "Fev"


def test_parse_tab_preserves_orig_coords():
    matrix = [
        ["nome", "valor"],
        ["Jacob", "999"],
    ]
    blocks = parse_tab(matrix)
    cell = blocks[0].rows[0]["valor"]
    assert cell.orig_row is not None
    assert cell.orig_col is not None


def test_parse_tab_mid_sheet_title():
    matrix = [
        ["nome", "cargo"],
        ["Jacob", "Closer"],
        ["BLOCO 2"],             # mid-sheet title
        ["nome", "cargo"],
        ["Alex", "Closer"],
    ]
    blocks = parse_tab(matrix)
    # Should produce at least 1 block with Jacob
    names = [r["nome"].value for b in blocks for r in b.rows]
    assert "Jacob" in names
