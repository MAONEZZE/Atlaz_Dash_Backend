from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

import pytz

_TZ_BR = pytz.timezone("America/Sao_Paulo")


def _current_month_bounds() -> tuple[datetime, datetime]:
    """Return (start, end) of current month in UTC, using America/Sao_Paulo for boundary."""
    now_br = datetime.now(_TZ_BR)
    start_br = now_br.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    if now_br.month == 12:
        end_br = now_br.replace(year=now_br.year + 1, month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
    else:
        end_br = now_br.replace(month=now_br.month + 1, day=1, hour=0, minute=0, second=0, microsecond=0)
    return start_br.astimezone(timezone.utc), end_br.astimezone(timezone.utc)


def _ms_to_utc(ms: Optional[int]) -> Optional[datetime]:
    if ms is None:
        return None
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc)


@dataclass
class PeriodClassification:
    current: bool
    past: bool
    current_range: Optional[tuple[datetime, datetime]]
    past_range: Optional[tuple[datetime, datetime]]


def classify_period(
    start_ms: Optional[int] = None,
    end_ms: Optional[int] = None,
) -> PeriodClassification:
    """
    Classify the requested [start_ms, end_ms] period relative to the current month
    (America/Sao_Paulo timezone).

    Returns flags:
      current=True  → range overlaps current month  → query n8n
      past=True     → range covers days before current month start → query Supabase
    Both can be True (mixed period).
    If no dates provided, defaults to current month only.
    """
    cur_start, cur_end = _current_month_bounds()

    req_start = _ms_to_utc(start_ms) if start_ms is not None else cur_start
    req_end = _ms_to_utc(end_ms) if end_ms is not None else cur_end

    # Clamp end to now if future
    now_utc = datetime.now(timezone.utc)
    if req_end > now_utc:
        req_end = now_utc

    overlaps_current = req_start < cur_end and req_end > cur_start
    has_past = req_start < cur_start

    current_range: Optional[tuple[datetime, datetime]] = None
    past_range: Optional[tuple[datetime, datetime]] = None

    if overlaps_current:
        current_range = (max(req_start, cur_start), min(req_end, cur_end))

    if has_past:
        past_range = (req_start, min(req_end, cur_start))

    return PeriodClassification(
        current=overlaps_current,
        past=has_past,
        current_range=current_range,
        past_range=past_range,
    )
