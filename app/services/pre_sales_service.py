"""
Pre-sales service — reads BASE_VENDAS tab, extracts funnel data by channel.
Returns all 5 channels (linkedin, instagram, indicacao, whatsapp, outros) with zeroed defaults.
"""

from loguru import logger

from app.core.config import settings
from app.dtos.pre_sales_dto import PreSalesResponseDTO
from app.services.google_sheets_service import read_tab
from app.services.sheet_parser_service import parse_tab


def get_pre_sales_funnels() -> PreSalesResponseDTO:
    """
    Read BASE_VENDAS tab, extract funnel data by channel.
    All 5 channels always present; zeroed when no data.
    Returns safe defaults on error.
    """
    try:
        matrix = read_tab(settings.default_spreadsheet_id, "BASE_VENDAS")
        blocks = parse_tab(matrix)

        # Phase 2: Full implementation would parse channel-specific funnel data from blocks.
        # For now, return default response with all 5 channels (zeroed).
        return PreSalesResponseDTO()
    except Exception as exc:
        logger.warning("pre_sales_service: failed to read/parse BASE_VENDAS | error={}", str(exc))
        return PreSalesResponseDTO()
