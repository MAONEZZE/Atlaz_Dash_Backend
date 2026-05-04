import math
import pytest
from app.utils.normalize_number import normalize_number


@pytest.mark.parametrize("raw,expected", [
    (0, 0),
    (42, 42),
    ("42", 42.0),
    ("42,5", 42.5),
    (None, 0),
    ("", 0),
    ("-", 0),
    (float("nan"), 0),
    (float("inf"), 0),
    ("abc", 0),
])
def test_normalize_number(raw, expected):
    result = normalize_number(raw)
    assert result == expected
    assert not (isinstance(result, float) and math.isnan(result))
