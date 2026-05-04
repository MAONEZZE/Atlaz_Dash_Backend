"""
Debug routes — NOT for frontend use.
Gated by DEBUG_ROUTES_ENABLED env variable (default false).
Exposes raw + parsed + normalized sheet data for development.
"""
from fastapi import APIRouter, HTTPException

from app.core.config import settings
from app.services.google_sheets_service import read_tab
from app.services.sheet_parser_service import extract_schema_info, parse_tab
from app.services.normalization_service import normalize_matrix

router = APIRouter(prefix="/debug", tags=["debug"])


def _guard():
    if not settings.debug_routes_enabled:
        raise HTTPException(status_code=404, detail="Not found")


@router.get("/sheets/{tab}/raw")
async def raw_sheet(tab: str) -> dict:
    """Return raw matrix from Google Sheets tab. Debug only."""
    _guard()
    matrix = read_tab(settings.default_spreadsheet_id, tab)
    return {"tab": tab, "rows": len(matrix), "data": matrix}


@router.get("/sheets/{tab}/schema")
async def sheet_schema(tab: str) -> dict:
    """Return detected schema info: headers, empty rows/cols, financial/date/month candidates, warnings."""
    _guard()
    matrix = read_tab(settings.default_spreadsheet_id, tab)
    info = extract_schema_info(matrix)
    return {"tab": tab, **info}


@router.get("/sheets/{tab}/normalized")
async def normalized_sheet(tab: str) -> dict:
    """Return normalized rows (post-parser, pre-DTO). Debug only."""
    _guard()
    matrix = read_tab(settings.default_spreadsheet_id, tab)
    blocks = parse_tab(matrix)
    normalized = normalize_matrix(blocks)
    return {"tab": tab, "blocks": len(blocks), "data": normalized}
