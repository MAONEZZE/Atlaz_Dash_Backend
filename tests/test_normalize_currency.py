import pytest
from app.utils.normalize_currency import normalize_currency


@pytest.mark.parametrize("raw,expected", [
    ("R$ 1.500,00", 1500.0),
    ("1.500,00", 1500.0),
    ("1500,00", 1500.0),
    ("1500", 1500.0),
    (1500, 1500.0),
    (1500.0, 1500.0),
    ("R$ 0,00", 0.0),
    (None, 0.0),
    ("", 0.0),
    ("abc", 0.0),
    (float("nan"), 0.0),
])
def test_normalize_currency(raw, expected):
    assert normalize_currency(raw) == expected
