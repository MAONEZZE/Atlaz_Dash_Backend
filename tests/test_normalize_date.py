from datetime import datetime, timezone
from app.utils.normalize_date import normalize_date


def test_ms_timestamp():
    dt = normalize_date(1746057600000)
    assert dt is not None
    assert dt.year == 2025


def test_ddmmyyyy():
    dt = normalize_date("01/05/2026")
    assert dt == datetime(2026, 5, 1, tzinfo=timezone.utc)


def test_iso():
    dt = normalize_date("2026-05-01")
    assert dt is not None
    assert dt.year == 2026 and dt.month == 5


def test_pt_short():
    dt = normalize_date("mai/2026")
    assert dt == datetime(2026, 5, 1, tzinfo=timezone.utc)


def test_pt_long():
    dt = normalize_date("maio 2026")
    assert dt == datetime(2026, 5, 1, tzinfo=timezone.utc)


def test_none():
    assert normalize_date(None) is None


def test_empty():
    assert normalize_date("") is None
