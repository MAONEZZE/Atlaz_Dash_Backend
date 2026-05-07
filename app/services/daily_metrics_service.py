"""
Daily metrics service — reads "Métricas Diárias" from Google Sheets in parallel.

Replaces the n8n statistics webhook for current-month data.

Each configured sheet (see settings.daily_metrics_sources) is read concurrently.
Rows are filtered to the requested [start_ms, end_ms] window, then summed per person.
Jennifer appears in 2 sheets (Jacob and Alex sheets) — her SDR metrics are merged by summing.
"""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from typing import Optional

from loguru import logger

from app.core.config import settings
from app.services.daily_metrics_sheet_parser import parse_daily_metrics
from app.services.google_sheets_service import read_tab
from app.services.statistics_service import (
    NormalizedCloserStats,
    NormalizedSdrStats,
    NormalizedStatistics,
    _merge_closer,
    _merge_sdr,
)
from app.utils.normalize_date import normalize_date
from app.utils.normalize_text import normalize_for_compare

_executor = ThreadPoolExecutor(max_workers=6)


def _parse_row_date_ms(date_str: str) -> Optional[int]:
    """
    Parse a date string from the sheet's first column and return UTC milliseconds.

    Accepts:
      - dd/mm          → inferred current year (e.g. "01/05")
      - d or dd        → day number (inferred current month and year)
      - Any format supported by normalize_date
    Returns None if the date cannot be parsed.
    """
    if not date_str or not date_str.strip():
        return None

    raw = date_str.strip()

    # Try normalize_date first (handles yyyy-mm-dd, dd/mm/yyyy, timestamps, etc.)
    dt = normalize_date(raw)
    if dt is not None:
        return int(dt.timestamp() * 1000)

    # Try "dd/mm" without year — assume current year
    import re
    if re.match(r"^\d{1,2}/\d{1,2}$", raw):
        try:
            day_str, month_str = raw.split("/")
            now = datetime.now(timezone.utc)
            dt = datetime(now.year, int(month_str), int(day_str), tzinfo=timezone.utc)
            return int(dt.timestamp() * 1000)
        except (ValueError, OverflowError):
            pass

    # Try plain day number (integer) — assume current month and year
    if re.match(r"^\d{1,2}$", raw):
        try:
            now = datetime.now(timezone.utc)
            dt = datetime(now.year, now.month, int(raw), tzinfo=timezone.utc)
            return int(dt.timestamp() * 1000)
        except (ValueError, OverflowError):
            pass

    return None


def _read_sheet_sync(sheet_id: str, tab_name: str) -> list[list]:
    """Synchronous wrapper around read_tab — runs in a thread pool executor."""
    return read_tab(spreadsheet_id=sheet_id, tab_name=tab_name)


def _sum_values(a: dict[str, int], b: dict[str, int]) -> dict[str, int]:
    """Merge two value dicts by summing matching keys."""
    result = dict(a)
    for key, val in b.items():
        result[key] = result.get(key, 0) + val
    return result


def _aggregate_sdr_rows(
    name: str,
    filtered_values: list[dict[str, int]],
) -> NormalizedSdrStats:
    """Sum all filtered daily rows into a single NormalizedSdrStats for one SDR."""
    totals: dict[str, int] = {}
    for row_values in filtered_values:
        totals = _sum_values(totals, row_values)

    return NormalizedSdrStats(
        nome=name,
        conexoes_enviadas=totals.get("conexoes_enviadas", 0),
        conexoes_aceitas=totals.get("conexoes_aceitas", 0),
        abordagens=totals.get("abordagens", 0),
        inmails_enviados=totals.get("inmails_enviados", 0),
        follow_ups=totals.get("follow_ups", 0),
        numeros_captados=totals.get("numeros_captados", 0),
        ligacoes_agendadas=totals.get("ligacoes_agendadas", 0),
        reunioes_agendadas=totals.get("reunioes_agendadas", 0),
        indicacoes_captadas=totals.get("indicacoes_captadas", 0),
    )


def _aggregate_closer_rows(
    name: str,
    filtered_values: list[dict[str, int]],
) -> NormalizedCloserStats:
    """Sum all filtered daily rows into a single NormalizedCloserStats for one Closer."""
    totals: dict[str, int] = {}
    for row_values in filtered_values:
        totals = _sum_values(totals, row_values)

    return NormalizedCloserStats(
        nome=name,
        ligacoes_realizadas=totals.get("ligacoes_realizadas", 0),
        reunioes_agendadas=totals.get("reunioes_agendadas", 0),
        reunioes_realizadas=totals.get("reunioes_realizadas", 0),
        indicacoes=totals.get("indicacoes", 0),
    )


def _filter_rows_by_date(
    daily_rows: list,
    start_ms: Optional[int],
    end_ms: Optional[int],
) -> list[dict[str, int]]:
    """
    Return the values dicts for daily rows that fall within [start_ms, end_ms].
    Rows whose date cannot be parsed are included (no date filter applied to them).
    If both start_ms and end_ms are None, all rows are included.
    """
    results = []
    for row in daily_rows:
        if start_ms is None and end_ms is None:
            results.append(row.values)
            continue

        row_ms = _parse_row_date_ms(row.date)
        if row_ms is None:
            # Cannot determine date — include row to be safe
            results.append(row.values)
            continue

        if start_ms is not None and row_ms < start_ms:
            continue
        if end_ms is not None and row_ms > end_ms:
            continue

        results.append(row.values)

    return results


async def fetch_current_month_from_sheets(
    start_ms: Optional[int] = None,
    end_ms: Optional[int] = None,
) -> NormalizedStatistics:
    """
    Read all configured "Métricas Diárias" spreadsheets in parallel.

    For each source (see settings.daily_metrics_sources):
      - Reads the sheet in a thread executor (non-blocking)
      - Parses closer and SDR sections
      - Filters rows to the [start_ms, end_ms] range
      - Aggregates daily values per person

    Jennifer appears in 2 sheets — her SDR metrics are summed across sheets.

    Returns NormalizedStatistics. Returns empty NormalizedStatistics if no sheets
    are configured or all reads fail.
    """
    sources = settings.daily_metrics_sources
    if not sources:
        logger.info("daily_metrics_service: no sheets configured — returning empty stats")
        return NormalizedStatistics()

    tab_name = settings.daily_metrics_tab_name
    loop = asyncio.get_running_loop()

    # Launch all sheet reads concurrently
    read_tasks = [
        loop.run_in_executor(_executor, _read_sheet_sync, source["sheet_id"], tab_name)
        for source in sources
    ]

    # Use gather with return_exceptions for graceful error handling per sheet
    gather_results = await asyncio.gather(*read_tasks, return_exceptions=True)

    # Accumulators: name → stats (for merging Jennifer across sheets)
    sdr_map: dict[str, NormalizedSdrStats] = {}
    closer_map: dict[str, NormalizedCloserStats] = {}

    for i, result in enumerate(gather_results):
        source = sources[i]
        sheet_id = source["sheet_id"]
        closer_name: str = source["closer"]
        sdr_name: str = source["sdr"]

        if isinstance(result, Exception):
            logger.warning(
                "daily_metrics_service: sheet read failed | sheet_id={} | type={} | detail={}",
                sheet_id,
                type(result).__name__,
                str(result),
            )
            continue

        matrix: list[list] = result  # type: ignore[assignment]

        # --- Parse CLOSER metrics ---
        try:
            closer_sheet = parse_daily_metrics(matrix, role="closer")
            closer_filtered = _filter_rows_by_date(closer_sheet.daily_rows, start_ms, end_ms)
            closer_stats = _aggregate_closer_rows(closer_name, closer_filtered)

            if closer_name in closer_map:
                closer_map[closer_name] = _merge_closer(closer_map[closer_name], closer_stats)
            else:
                closer_map[closer_name] = closer_stats
        except Exception as exc:
            logger.warning(
                "daily_metrics_service: closer parse failed | sheet_id={} | closer={} | detail={}",
                sheet_id, closer_name, str(exc),
            )

        # --- Parse SDR metrics ---
        try:
            sdr_sheet = parse_daily_metrics(matrix, role="sdr")
            sdr_filtered = _filter_rows_by_date(sdr_sheet.daily_rows, start_ms, end_ms)
            sdr_stats = _aggregate_sdr_rows(sdr_name, sdr_filtered)

            if sdr_name in sdr_map:
                # Jennifer (and any other repeated SDR) — sum across sheets
                sdr_map[sdr_name] = _merge_sdr(sdr_map[sdr_name], sdr_stats)
            else:
                sdr_map[sdr_name] = sdr_stats
        except Exception as exc:
            logger.warning(
                "daily_metrics_service: sdr parse failed | sheet_id={} | sdr={} | detail={}",
                sheet_id, sdr_name, str(exc),
            )

    return NormalizedStatistics(
        sdr=list(sdr_map.values()),
        closer=list(closer_map.values()),
    )
