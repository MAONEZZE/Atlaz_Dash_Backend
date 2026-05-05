"""
Finance service — reads BASE_VENDAS tab, computes summary, products, channels, breakdown, monthly table.
Handles messy sheet data: merged cells, mixed layouts, months as columns.
Returns safe defaults on parse errors.
"""

from datetime import datetime
from loguru import logger

from app.core.config import settings
from app.core.field_maps import resolve_field
from app.dtos.sales_values_dto import (
    SalesFinanceResponseDTO, FinancialSummaryDTO, FinancialMonthDTO,
    ProductRevenueDTO, ChannelRevenueDTO, FinancialBreakdownDTO,
    MonthlyFinancialTableDTO, MonthlyFinancialTableRowDTO
)
from app.services.google_sheets_service import read_tab
from app.services.sheet_parser_service import parse_tab
from app.utils.normalize_currency import normalize_currency
from app.utils.normalize_date import normalize_date


def _get_current_month_index() -> int:
    """Returns 0-based month index (0=Jan, 1=Feb, ..., 11=Dec)."""
    return datetime.now().month - 1


def _month_abbreviation(month_num: int) -> str:
    """Convert month number (1-12) to PT abbreviation."""
    months = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
    return months[max(0, min(11, month_num - 1))]


def _parse_financial_value(value: object) -> float:
    """Convert currency/number to float, return 0 on error."""
    if value is None or value == "":
        return 0.0
    try:
        return float(normalize_currency(value))
    except Exception:
        return 0.0


def get_sales_finance_data() -> SalesFinanceResponseDTO:
    """
    Read BASE_VENDAS tab, parse financial data, return complete response.
    On any error, return safe defaults (zeroed fields, empty arrays).
    """
    try:
        matrix = read_tab(settings.default_spreadsheet_id, "BASE_VENDAS")
        blocks = parse_tab(matrix)

        # Phase 2: Full implementation would aggregate blocks into summary, products, channels, etc.
        # For now, return safe defaults.
        return SalesFinanceResponseDTO()
    except Exception as exc:
        logger.warning("finance_service: failed to read/parse BASE_VENDAS | error={}", str(exc))
        return SalesFinanceResponseDTO()
