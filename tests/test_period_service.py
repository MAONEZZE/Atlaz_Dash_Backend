from datetime import datetime, timezone, timedelta
from unittest.mock import patch
import pytz
from app.services.period_service import classify_period

_TZ_BR = pytz.timezone("America/Sao_Paulo")


def _ms(dt: datetime) -> int:
    return int(dt.timestamp() * 1000)


def _now_br() -> datetime:
    return datetime.now(_TZ_BR)


def test_no_dates_defaults_to_current():
    result = classify_period()
    assert result.current is True
    assert result.past is False
    assert result.current_range is not None
    assert result.past_range is None


def test_fully_current_month():
    now_br = _now_br()
    start = now_br.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    end = now_br
    result = classify_period(_ms(start), _ms(end))
    assert result.current is True
    assert result.past is False


def test_fully_past():
    # January 2024
    start = datetime(2024, 1, 1, tzinfo=timezone.utc)
    end = datetime(2024, 1, 31, tzinfo=timezone.utc)
    result = classify_period(_ms(start), _ms(end))
    assert result.current is False
    assert result.past is True
    assert result.past_range is not None


def test_mixed_period():
    # Start last month, end this month
    now_br = _now_br()
    cur_start_br = now_br.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    prev_month_start = (cur_start_br - timedelta(days=1)).replace(day=1)
    result = classify_period(_ms(prev_month_start), _ms(now_br))
    assert result.current is True
    assert result.past is True
    assert result.current_range is not None
    assert result.past_range is not None


def test_missing_end_date():
    now_br = _now_br()
    start = now_br.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    result = classify_period(_ms(start), None)
    assert result.current is True
