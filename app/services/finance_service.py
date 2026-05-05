"""
Finance service — reads BASE_VENDAS tab, returns financial data.
Full parsing deferred pending BASE_VENDAS structure validation.
Returns safe defaults on any error.
"""

from loguru import logger

from app.core.config import settings
from app.dtos.sales_values_dto import SalesFinanceResponseDTO
from app.services.google_sheets_service import read_tab
from app.services.sheet_parser_service import parse_tab


def get_sales_finance_data() -> SalesFinanceResponseDTO:
    """Read BASE_VENDAS tab. Returns safe defaults on any error."""
    try:
        matrix = read_tab(settings.default_spreadsheet_id, "BASE_VENDAS")
        _blocks = parse_tab(matrix)
        return SalesFinanceResponseDTO()
    except Exception as exc:
        logger.warning("finance_service: failed to read/parse BASE_VENDAS | error={}", str(exc))
        return SalesFinanceResponseDTO()
