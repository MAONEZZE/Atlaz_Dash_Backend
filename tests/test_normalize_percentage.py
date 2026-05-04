import pytest
from app.utils.normalize_percentage import normalize_percentage


@pytest.mark.parametrize("raw,as_fraction,expected", [
    ("10%", False, 10.0),
    ("10,5%", False, 10.5),
    ("10%", True, 0.10),
    (0.10, False, 0.10),
    (10, False, 10.0),
    (None, False, 0.0),
    ("", False, 0.0),
])
def test_normalize_percentage(raw, as_fraction, expected):
    assert normalize_percentage(raw, as_fraction=as_fraction) == pytest.approx(expected, rel=1e-6)
